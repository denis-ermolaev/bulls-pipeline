import logging
import os
import re
import subprocess
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Callable, List

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy.stats import chi2
from tqdm import tqdm

logger = logging.getLogger(__name__)
load_dotenv()


class CMD:
    # TODO: Отчистка tmp файлов, после завершения работы python
    def __init__(self):
        # Общие пути
        self.data_dir = Path(os.getenv("PATH_VCF_SEP"))
        """Папка с отдельными .vcf для каждой коровы"""

        self.output_dir = Path(os.getenv("PATH_VCF"))
        """Папка с результатами объединения vcf файлов"""

        self.imputation_dir = Path(os.getenv("PATH_IMPUTATION"))
        """Папка с результатами импутации"""

        self.gwas_dir = Path(os.getenv("PATH_GWAS"))
        """Папка с результатами gwas"""

        # Пути к конкретным файлам
        self.merged_vcf_file = self.output_dir / "merged.vcf.gz"

        # Программы
        self.bgzip = os.getenv("BGZIP")
        self.bcftools = os.getenv("BCFTOOLS")
        self.plink = os.getenv("PLINK")
        self.beagle = os.getenv("BEAGLE")
        self.regenie = os.getenv("REGENIE")

        # Переопределение путей для TEST режима
        test_mode = True if os.getenv("TEST_MODE", "False") == "True" else False
        if test_mode:
            self.data_dir = Path(os.getenv("PATH_VCF_SEP_TEST"))
            self.output_dir = Path(os.getenv("PATH_VCF_TEST"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def parallel_run(
        func: Callable[[Any], Any],
        objects: List[Any],
        processes: int = 1,
    ):
        """
        Параллельно запустить ф-ю на нескольких значениях (object)
        Может использоваться для запуска ф-и для нескольких файлов параллельно
        """
        with Pool(processes) as p:
            result = p.map(func, objects)
        return result

    @staticmethod
    def run_command(cmd):
        # TODO: Сделать передачу cmd через словарь, который потом парсится в список
        logger.debug(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed with code {result.returncode}")
            if result.stderr.strip():
                logger.error(f"STDERR:\n{result.stderr}")
            if result.stdout.strip():
                logger.error(f"STDOUT:\n{result.stdout}")
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
                        subprocess.run(
                            [self.bgzip, "-c", str(vcf)], stdout=f_out, check=True
                        )
                    os.replace(tmp_gz_file, gz_file)
                except (Exception, KeyboardInterrupt) as e:
                    # Если прервали (Ctrl+C), удаляем мусор
                    if Path(tmp_gz_file).exists():
                        os.remove(tmp_gz_file)
                    print(f"Ошибка при сжатии: {e}")

            if not Path(csi_file).exists():
                try:
                    # Пишем во временный файл
                    self.run_command(
                        [self.bcftools, "index", "-f", gz_file, "-o", tmp_csi_file]
                    )
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
            logger.debug(
                f"Путь до merge файла: {Path(output_path)}, {Path(output_path)}"
            )
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
                    "-Oz",  # Уже сжатый файл
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
        """
        Создание необходимых для GWAS файлов
        covariates.txt
        phenotype.txt
        """
        try:
            self.merge_vcf_path = self.merge_vcf_path
        except AttributeError:
            # TODO: получать из .env
            self.merge_vcf_path = "/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz"
        logger.info("Конвертация в формат для plink...")
        out_prefix = self.output_dir / out_name

        # Если последний файл результата есть, то прекратить выполнение ф-и
        if Path(f"{self.output_dir}/phenotype.txt").exists():
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

        # Отчистка
        self.run_command(
            [
                self.plink,
                "--bfile",
                f"{str(out_prefix)}",
                "--memory",
                "5000",
                "--chr-set",  # На всех 31 хромосомах
                "31",
                "--maf",
                "0.01",  # Для более точного расчёта родства ?
                "--geno",
                "0.5",
                "--mind",
                "0.5",
                "--make-bed",
                "--out",
                f"{str(self.output_dir)}/clean_{out_name}",
            ]
        )

        # Убрать SNP с сцеплением LD
        self.run_command(
            [
                self.plink,
                "--bfile",
                f"{str(self.output_dir)}/clean_{out_name}",
                "--memory",
                "5000",
                "--chr-set",
                "31",  # На всех 31 хромосомах
                "--indep-pairwise",
                "50",
                "5",
                "0.2",
                "--out",
                f"{self.output_dir}/prunning_list",
            ]
        )

        #     plink --bfile step1_qc \
        #   --extract step1_prune.prune.in \
        #   --make-bed \
        #   --out results/gwas/step1_snps
        self.run_command(
            [
                self.plink,
                "--bfile",
                f"{str(self.output_dir)}/clean_{out_name}",
                "--memory",
                "50000",
                "--chr-set",
                "31",
                "--chr",
                "1-29",
                "--extract",
                f"{str(self.output_dir) + '/prunning_list'}.prune.in",
                "--make-bed",
                "--out",
                f"{str(self.output_dir)}/clean_{out_name}_1_29_prune",
            ]
        )

        # PCA
        self.run_command(
            [
                self.plink,
                "--bfile",
                f"{str(self.output_dir)}/clean_{out_name}",
                "--memory",
                "5000",
                "--chr-set",
                "31",  # На всех 31 хромосомах
                "--extract",
                f"{str(self.output_dir) + '/prunning_list'}.prune.in",
                "--pca",
                "5",
                "--out",
                f"{self.output_dir}/bulls_pca",
            ]
        )

        # Ковариаты
        df_covariates = pd.read_csv(
            f"{self.output_dir}/bulls_pca.eigenvec", sep=" ", header=None
        )
        columns = list(range(1, len(df_covariates.columns) - 1))
        columns = ["FID", "IID"] + [f"V{i}" for i in columns]
        df_covariates.columns = columns
        df_covariates.to_csv(f"{self.output_dir}/covariates.txt", sep=" ", index=False)

        # Фенотипы
        df_phenotype = pd.read_csv(
            "/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/all_phenotypes.csv"
        )
        columns = list(df_phenotype.columns)
        columns[0] = "IID"

        df_phenotype.columns = columns

        df_phenotype["FID"] = df_phenotype["IID"]

        df_phenotype = df_phenotype[["FID", "IID", "Yield", "Fat", "Protein"]].copy()
        for column in ["Yield", "Fat", "Protein"]:
            df_phenotype[column] = df_phenotype[column].fillna("NA")
        # пример на Python
        import numpy as np
        from scipy.stats import norm, rankdata

        df_phenotype["Yield_norm"] = norm.ppf(
            (rankdata(df_phenotype["Yield"]) - 0.5) / len(df_phenotype)
        )
        df_phenotype["random_phenotype"] = np.random.normal(0, 1, len(df_phenotype))
        df_phenotype.to_csv(f"{self.output_dir}/phenotype.txt", sep=" ", index=False)

    def imputation(self):
        """
        Обёртка для импутации сразу нескольких хромосом
        """
        objects = list(range(1, 30))  # 29 хромосом

        self.parallel_run(self._imputation, objects, 4)

    def _imputation(self, num_chr: int):
        try:
            self.merge_vcf_path = self.merge_vcf_path
        except AttributeError:
            # TODO: получать из .env
            self.merge_vcf_path = "/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz"
        # Создание папки с разделёнными хромосомами
        if not Path(
            "/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes"
        ).exists():
            self.run_command(
                [
                    "mkdir",
                    "-p",
                    "/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes",
                ]
            )

        # Разделение хромосом
        output_path = f"/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr{num_chr}.vcf.gz"
        output_path_tmp = f"/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr{num_chr}.vcf.gz.tmp"
        if not Path(
            f"{output_path}.csi"
        ).exists():  # Проверка по конечной операции, а именно появлению индекса
            cmd = [
                self.bcftools,
                "view",
                "-r",
                str(num_chr),
                str(self.merge_vcf_path),
                "-Oz",  # Уже сжатый файл
                "-o",
                output_path_tmp,
            ]
            if self.run_command(cmd):
                # Индексация финального файла
                self.run_command([self.bcftools, "index", "-c", str(output_path_tmp)])
                os.replace(output_path_tmp, output_path)
                os.replace(f"{output_path_tmp}.csi", f"{output_path}.csi")

        output_path = f"/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr{num_chr}/chr{num_chr}"
        output_path_tmp = f"/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr{num_chr}/chr{num_chr}.tmp"
        if not Path(f"{output_path}_filtered.vcf.gz").exists():  # По последней операции
            self.run_command(
                [
                    "mkdir",
                    "-p",
                    f"/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr{num_chr}",
                ]
            )
            cmd = [
                "java",
                "-Xmx100g",
                "-jar",
                self.beagle,
                f"ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr{num_chr}_phased_snp.vcf.gz",
                f"gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr{num_chr}.vcf.gz",
                f"map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps_holstein/chr{num_chr}.map",
                f"out={output_path_tmp}",
                f"chrom={num_chr}",
                "nthreads=6",
                "ne=50000",
                "cluster=0.005",
                "window=200",
                "em=false",
                "impute=true",
            ]
            if self.run_command(cmd):
                # Индексация финального файла
                self.run_command(
                    [self.bcftools, "index", "-c", str(f"{output_path_tmp}.vcf.gz")]
                )
                self.run_command(
                    [
                        self.bcftools,
                        "view",
                        "-G",
                        f"{output_path_tmp}.vcf.gz",
                        "-Oz",
                        "-o",
                        f"{output_path_tmp}_for_analysis.vcf.gz",
                    ]
                )
                # /opt/tools/bin/bcftools view -i 'INFO/DR2>=0.7' -Oz -o "${f%.vcf.gz}_filtered.vcf.gz" "$f"
                self.run_command(
                    [
                        self.bcftools,
                        "view",
                        "-i",
                        "INFO/DR2>=0.7",  # Условие фильтра без кавычек
                        f"{output_path_tmp}.vcf.gz",
                        "-Oz",
                        "-o",
                        f"{output_path_tmp}_filtered.vcf.gz",
                    ]
                )

                os.replace(f"{output_path_tmp}.vcf.gz", f"{output_path}.vcf.gz")
                os.replace(f"{output_path_tmp}.log", f"{output_path}.log")
                os.replace(
                    f"{output_path_tmp}.vcf.gz.csi",
                    f"{output_path}.vcf.gz.csi",
                )
                # for_analysis - для быстрого получения статистики по DR2 и т.п
                os.replace(
                    f"{output_path_tmp}_for_analysis.vcf.gz",
                    f"{output_path}_for_analysis.vcf.gz",
                )
                # filtered - для последующего использования в gwas(Оставляет только качественно импутированные SNP)
                os.replace(
                    f"{output_path_tmp}_filtered.vcf.gz",
                    f"{output_path}_filtered.vcf.gz",
                )

    def pre_gwas(self):
        objects = sorted(
            [
                int(re.search(r"\d{1,2}", file.name)[0])
                for dir in self.imputation_dir.iterdir()
                if dir.is_dir()
                for file in dir.iterdir()
                if file.is_file()
                and str(file.name).find("_filtered") != -1
                and str(file.name).find("tmp") == -1
            ]
        )
        self.parallel_run(self._pre_gwas, objects, 5)

    def _pre_gwas(self, num_chr: int):
        input_file = f"{self.imputation_dir}/chr{num_chr}/chr{num_chr}_filtered.vcf.gz"
        output_dir = f"{self.gwas_dir}/chr{num_chr}"

        if not Path(output_dir).exists():
            self.run_command(
                [
                    "mkdir",
                    "-p",
                    f"{output_dir}",
                ]
            )

        if not Path(f"{output_dir}/plink_chr{num_chr}").with_suffix(".bed").exists():
            # Конвертация в формат plink
            self.run_command(
                [
                    self.plink,
                    "--chr-set",
                    "29",
                    "--make-bed",
                    "--memory",
                    "80000",
                    "--vcf",
                    f"{input_file}",
                    "--out",
                    f"{output_dir}/plink_chr{num_chr}",
                ]
            )
        if (
            not Path(f"{output_dir}/plink_filtered_chr{num_chr}")
            .with_suffix(".bed")
            .exists()
        ):
            # Отчистка
            self.run_command(
                [
                    self.plink,
                    "--bfile",
                    f"{output_dir}/plink_chr{num_chr}",
                    "--memory",
                    "80000",
                    "--chr-set",
                    "29",
                    "--maf",
                    "0.1",
                    "--geno",
                    "0.05",
                    "--mind",
                    "0.05",
                    "--make-bed",
                    "--out",
                    f"{output_dir}/plink_filtered_chr{num_chr}",
                ]
            )

    def pre_gwas_merge(self):
        # Закончить выполнение ф-и, если конечный результат уже есть
        if Path(f"{self.gwas_dir}/merged_prune").with_suffix(".bed").exists():
            return True
        all_file = [
            str(file.with_suffix(""))
            for dir in self.gwas_dir.iterdir()
            if dir.is_dir()
            for file in dir.iterdir()
            if file.is_file() and re.match(r".*plink_filtered_chr.*?\.bed", str(file))
        ]
        all_file = sorted(all_file)

        Path(f"{self.gwas_dir}/merge_list.txt").write_text("\n".join(all_file))

        self.run_command(
            [
                self.plink,
                "--memory",
                "80000",
                "--chr-set",
                "29",
                "--merge-list",
                f"{self.gwas_dir}/merge_list.txt",
                "--make-bed",
                "--out",
                f"{self.gwas_dir}/merged",
            ]
        )

        self.run_command(
            [
                self.plink,
                "--bfile",
                f"{self.gwas_dir}/merged",
                "--memory",
                "80000",
                "--chr-set",
                "29",
                "--indep-pairwise",
                "50",
                "5",
                "0.2",
                "--out",
                f"{self.gwas_dir}/prunning_list",
            ]
        )

        #     plink --bfile step1_qc \
        #   --extract step1_prune.prune.in \
        #   --make-bed \
        #   --out results/gwas/step1_snps
        self.run_command(
            [
                self.plink,
                "--bfile",
                f"{self.gwas_dir}/merged",
                "--memory",
                "80000",
                "--chr-set",
                "29",
                "--chr",
                "1-29",
                "--extract",
                f"{str(self.gwas_dir) + '/prunning_list'}.prune.in",
                "--make-bed",
                "--out",
                f"{self.gwas_dir}/merged_prune",
            ]
        )

    def gwas(self):
        if not Path(f"{self.gwas_dir}/step1_results_pred.list").exists():
            # Первый этап GWAS
            self.run_command(
                [
                    self.regenie,
                    "--step",
                    "1",
                    "--bed",
                    # f"{self.gwas_dir}/merged",
                    f"{self.gwas_dir}/merged_prune",
                    "--phenoFile",
                    f"{self.output_dir}/phenotype.txt",
                    "--covarFile",
                    f"{self.output_dir}/covariates.txt",
                    "--nauto",
                    "29",
                    "--bsize",
                    "1000",
                    "--lowmem",
                    "--threads",
                    "32",
                    "--out",
                    f"{self.gwas_dir}/step1_results",
                ]
            )

        if not Path(f"{self.gwas_dir}/final_gwas_results").with_suffix(".log").exists():
            # Второй этап GWAS
            self.run_command(
                [
                    self.regenie,
                    "--step",
                    "2",
                    "--bed",
                    f"{self.gwas_dir}/merged",
                    "--phenoFile",
                    f"{self.output_dir}/phenotype.txt",
                    "--covarFile",
                    f"{self.output_dir}/covariates.txt",
                    "--nauto",
                    "29",
                    "--bsize",
                    "400",
                    "--threads",
                    "32",
                    "--pred",
                    f"{self.gwas_dir}/step1_results_pred.list",
                    "--out",
                    f"{self.gwas_dir}/final_gwas_results",
                ]
            )

    def gwas_analysis(self):
        gwas_result = [
            file
            for file in self.gwas_dir.iterdir()
            if file.is_file() and file.suffix == ".regenie"
        ]
        suggestive_threshold = 1e-5

        for filepath in gwas_result:
            if filepath.with_suffix(".txt").exists():
                continue
            df = pd.read_csv(filepath, sep="\s+")
            if "LOG10P" in df.columns:
                df["P"] = np.power(10, -df["LOG10P"])
            elif "PVAL" in df.columns:
                df["P"] = df["PVAL"]
            elif "CHISQ" in df.columns:
                df["P"] = chi2.sf(df["CHISQ"], 1)
            else:
                raise ValueError("Нужны столбцы LOG10P, PVAL или CHISQ.")
            df["LOGP"] = -np.log10(df["P"])

            # Отбираем SNP, где P < порога
            sig_df = df[df["P"] < suggestive_threshold].copy()

            # Сортируем по P-value (от самых значимых к менее значимым)
            sig_df = sig_df.sort_values("P")["ID"]
            sig_df.to_csv(filepath.with_suffix(".txt"), header=False, index=False)

        objects = [i for i in range(1, 30)]

        self.parallel_run(self._ld_block, objects, 29)

    def _ld_block(self, num_chr: int):
        # bin/plink/plink --bfile /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/gwas/chr24/plink_filtered_chr24
        # --chr-set 29 --memory 80000 --blocks no-pheno-req
        # --out /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/gwas/chr24/snps_blocks
        if (
            not Path(f"{self.gwas_dir}/chr{num_chr}/snps_blocks")
            .with_suffix(".blocks.det")
            .exists()
        ):
            self.run_command(
                [
                    self.plink,
                    "--bfile",
                    f"{self.gwas_dir}/chr{num_chr}/plink_filtered_chr{num_chr}",
                    "--memory",
                    "80000",
                    "--chr-set",
                    "29",
                    "--blocks",
                    "no-pheno-req",
                    "--out",
                    f"{self.gwas_dir}/chr{num_chr}/snps_blocks",
                ]
            )
        # df = pd.read_csv(str(filepath.with_suffix(".ld")), sep=" ")


if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    cmd = CMD()
    cmd.prepare_vcf_files()
    cmd.merge_vcf()
    cmd.convert_to_plink()
    cmd.imputation()
    cmd.pre_gwas()
    cmd.pre_gwas_merge()
    cmd.gwas()
    cmd.gwas_analysis()
