import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)
load_dotenv()


class CMD:
    def __init__(self):
        # Обязательно оборачиваем в Path для работы .glob() и /
        self.data_dir = Path(os.getenv("PATH_VCF_SEP"))
        self.output_dir = Path(os.getenv("PATH_VCF"))

        self.bgzip = os.getenv("BGZIP")
        self.bcftools = os.getenv("BCFTOOLS")
        self.plink = os.getenv("PLINK")

        self.beagle = os.getenv("BEAGLE")
        self.regenie = os.getenv("REGENIE")

        test_mode = True if os.getenv('TEST_MODE', 'False') == "True" else False
        if test_mode:
            self.data_dir = Path(os.getenv("PATH_VCF_SEP_TEST"))
            self.output_dir = Path(os.getenv("PATH_VCF_TEST"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.merge_vcf_path: Path  # Объединённый vcf файл

    def run_command(self, cmd):
        logger.debug(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.debug(f"Error: {result.stderr}")
            return False
        return True

    def prepare_vcf_files(self):
        """Сжимает .vcf в .vcf.gz и индексирует их (аналог вашего цикла while)"""
        vcf_files = list(self.data_dir.glob("**/*.vcf"))
        logger.info("Сжатие и индексация vcf файлов...")

        for vcf in tqdm(vcf_files, total=len(vcf_files)):
            gz_file = f"{vcf}.gz"
            tmp_gz_file = gz_file + ".tmp"
            csi_file = f"{vcf}.gz.csi"
            tmp_csi_file = csi_file + ".tmp"

            if not Path(gz_file).exists():
                try:
                    # Пишем во временный файл
                    # Используем -c для вывода в stdout и аргумент stdout в subprocess
                    with open(tmp_gz_file, "wb") as f_out:
                        subprocess.run([self.bgzip, "-c", str(vcf)], stdout=f_out, check=True)
                    os.replace(tmp_gz_file, gz_file)
                except (Exception, KeyboardInterrupt) as e:
                    # Если прервали (Ctrl+C), удаляем мусор
                    if Path(tmp_gz_file).exists():
                        os.remove(tmp_gz_file)
                    print(f"Ошибка при сжатии: {e}")

            if not Path(csi_file).exists():
                try:
                    # Пишем во временный файл
                    self.run_command([self.bcftools, "index", "-f", gz_file, "-o", tmp_csi_file])
                    # Если всё прошло успешно (не прервано) — переименовываем
                    os.replace(tmp_csi_file, csi_file)
                except (Exception, KeyboardInterrupt) as e:
                    # Если прервали (Ctrl+C), удаляем мусор
                    if Path(tmp_csi_file).exists():
                        os.remove(tmp_csi_file)
                    print(f"Ошибка при сжатии: {e}")

    def merge_vcf(self, filename="merged.vcf.gz"):
        output_path = self.output_dir / filename
        output_path_tmp = output_path.with_suffix(output_path.suffix + ".tmp")
        gz_files = list(self.data_dir.glob("**/*vcf.gz"))
        list_file = self.output_dir / "vcf_file_list.txt"
        logger.info("Объединение всех vcf файлов и индексация финального файла...")

        if not Path(output_path).exists():
            logger.debug(f"Путь до merge файла: {Path(output_path)}, {Path(output_path)}")
            try:
                with open(list_file, "w") as f:
                    for gz in gz_files:
                        f.write(f"{gz.resolve()}\n")

                # Объединение
                cmd = [
                    self.bcftools,
                    "merge",
                    "-l",
                    str(list_file),
                    "-Oz", # Уже сжатый файл
                    "-o",
                    str(output_path_tmp),
                ]
                if self.run_command(cmd):
                    # Индексация финального файла
                    os.replace(output_path_tmp, output_path)
                    self.run_command([self.bcftools, "index", "-t", str(output_path)])
            except (Exception, KeyboardInterrupt) as e:
                    # Если прервали (Ctrl+C), удаляем мусор
                    if Path(output_path_tmp).exists():
                        os.remove(output_path_tmp)
                    print(f"Ошибка при сжатии: {e}")

        self.merge_vcf_path = output_path

    def convert_to_plink(self, out_name="merged_plink"):
        logger.info("Конвертация в формат для plink...")
        out_prefix = self.output_dir / out_name
        if Path(out_prefix).with_suffix('.bed').exists():
            return True

        # Plink сам создаёт временные файлы
        cmd = [
            self.plink,
            "--vcf",
            str(self.merge_vcf_path),
            "--make-bed",
            "--chr-set",
            "31",
            "--memory",
            "80000",
            "--out",
            str(out_prefix),
        ]
        self.run_command(cmd)
    def imputation(self):
        # self.output_dir
        # TODO:
        # TODO: понять сколько хромосом в файле
        # TODO: сделать импутацию по каждой хромосоме
        # TODO: отфильтровать результаты
        # TODO: сшить полученный файл
        pass


if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    cmd = CMD()
    cmd.prepare_vcf_files()
    cmd.merge_vcf()
    cmd.convert_to_plink()
