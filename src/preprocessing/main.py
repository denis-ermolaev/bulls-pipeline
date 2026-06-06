import logging
import os
from pathlib import Path

import pandas as pd
import pysam
from dotenv import load_dotenv
from tqdm import tqdm

import src.preprocessing.tools_genome as tools_genome

tqdm.pandas(disable=True)  # подключить поддержку progress_apply
load_dotenv()

logger = logging.getLogger(__name__)


def create_vcf_for_sample(sample_id, sample_df, name_file, path_to_result) -> str:
    """
    Создает VCF файл для одного образца(организма) на основе его данных в DataFrame.
    """
    filepath = f"{path_to_result}/{name_file}/{sample_id}.vcf"
    output_path = Path(f"{path_to_result}/{name_file}")
    # test_mode = test_mode = True if os.getenv("TEST_MODE", "False") == "True" else False
    # if test_mode:
    #     filepath = f"{os.getenv('PATH_VCF_SEP_TEST')}/{name_file}/{sample_id}.vcf"
    #     output_path = Path(f"{os.getenv('PATH_VCF_SEP_TEST')}/{name_file}")

    output_path.mkdir(parents=True, exist_ok=True)

    header = pysam.VariantHeader()

    for chrom in sample_df["Chr"].unique():
        header.add_meta("contig", items=[("ID", str(chrom))])

    header.add_meta(
        "FORMAT",
        items=[
            ("ID", "GT"),
            ("Number", "1"),
            ("Type", "String"),
            ("Description", "Genotype"),
        ],
    )

    header.add_sample(sample_id)

    vcf_out = pysam.VariantFile(filepath, "w", header=header)

    for row in sample_df.itertuples():
        record = vcf_out.new_record(
            contig=str(row.Chr),
            start=row.Position - 1,  # VCF POS (1-based) -> pysam start (0-based)
            alleles=(row.REF, row.ALT),
            id=row.SNP_Name,
        )

        record.filter.add("PASS")

        # --- ОПРЕДЕЛЕНИЕ ГЕНОТИПА ---
        complementarity = {"A": "T", "T": "A", "C": "G", "G": "C"}
        SNP_A = row.SNP.strip("[]").split("/")[0]
        SNP_B = row.SNP.strip("[]").split("/")[1]
        IlmnStrand = row.IlmnStrand
        RefStrand = row.RefStrand
        REF = row.REF
        alphabetical_order = ["A", "C", "G", "T"]  # Правильный ?

        if row.Allele1_AB != "-" and row.Allele2_AB != "-":
            if f"{SNP_A}/{SNP_B}" not in ["A/T", "C/G", "T/A", "G/C"]:
                if SNP_A == "A" or SNP_A == "T":
                    allele_A = SNP_A
                else:
                    allele_B = SNP_A
                if SNP_B == "C" or SNP_B == "G":
                    allele_B = SNP_B
                else:
                    allele_A = SNP_B
            elif f"{SNP_A}/{SNP_B}" in ["A/T", "C/G", "T/A", "G/C"]:
                num_SNP_A = alphabetical_order.index(SNP_A)  # 0, 1, 2, 3
                num_SNP_B = alphabetical_order.index(SNP_B)  # 0, 1, 2, 3

                if IlmnStrand == "TOP":
                    allele_A = SNP_A if num_SNP_A < num_SNP_B else SNP_B
                    allele_B = SNP_A if allele_A != SNP_A else SNP_B
                elif IlmnStrand == "BOT":
                    allele_A = SNP_A if num_SNP_A > num_SNP_B else SNP_B
                    allele_B = SNP_A if allele_A != SNP_A else SNP_B
            if RefStrand == "-":
                allele_A = complementarity[allele_A]
                allele_B = complementarity[allele_B]
            SNP_normal = {"A": allele_A, "B": allele_B}
            allele1 = 0 if SNP_normal[row.Allele1_AB] == REF else 1
            allele2 = 0 if SNP_normal[row.Allele2_AB] == REF else 1
            gt = tuple(sorted((allele1, allele2)))
            if REF not in (allele_A, allele_B):
                logger.error(
                    f"Предупреждение: REF {REF} не совпадает с аллелями {SNP_A}/{SNP_B} для SNP {row.SNP}"
                )
                record.samples[sample_id]["GT"] = (None, None)
            else:
                record.samples[sample_id]["GT"] = gt
        else:
            record.samples[sample_id]["GT"] = (None, None)

        vcf_out.write(record)

    vcf_out.close()

    return filepath


def create_column_REF(row):
    if row.Chr == "0" or row.Position == 0:
        return None
    return tools_genome.get_ref_base(row.Chr, row.Position)


def create_column_ALT(row):
    """
    Создание колонки с ALT аллелем
    """
    complementarity = {"A": "T", "T": "A", "C": "G", "G": "C"}
    if pd.isnull(row["REF"]) or pd.isnull(row["SNP"]) or pd.isnull(row["RefStrand"]):
        return "DATA_ERROR"

    ref_allele = row["REF"]
    snp = row["SNP"].strip("[]").split("/")
    ref_strand = row["RefStrand"]

    # ref_strand - указание для какой цепи ДНК(+-) указаны нуклеотиды в snp
    if ref_strand == "+":
        if ref_allele in snp:
            return snp[0] if snp[1] == ref_allele else snp[1]
        else:
            return "DATA_ERROR"
    elif ref_strand == "-":
        snp = [complementarity[snp[0]], complementarity[snp[1]]]
        if ref_allele in snp:
            return snp[0] if snp[1] == ref_allele else snp[1]
        else:
            return "DATA_ERROR"
    else:
        return "DATA_ERROR"


def process_file(
    input: dict[str, list[str]], output_dir: str
) -> dict[str, str | list[str]]:
    """
    Обработка одного файла
    """
    file_path = input["main"][0]
    path_to_result = output_dir
    # file_path, path_to_result
    # try:
    # file_name = f"{os.getenv('PATH_VCF_SEP')}/{name_file}"

    # test_mode = True if os.getenv("TEST_MODE", "False") == "True" else False
    # if test_mode:
    #     file_name = f"{os.getenv('PATH_VCF_SEP_TEST')}/{name_file}"
    logger.debug(f"[process_file]: {file_path}, {path_to_result}")
    bovinehd_manifest_df = pd.read_csv(  # pyright: ignore[reportCallIssue]
        os.getenv("MANIFEST_PATH"),
        sep=",",
        header=7,
        skipfooter=24,
        usecols=["Name", "IlmnStrand", "SNP", "RefStrand"],
        engine="python",
    )

    # if Path(file_path).exists():
    #     return None

    # pyarrow с 1 минуты 25 секунд до 25 секунд
    df = pd.read_csv(
        file_path,
        sep="\t",
        header=9,
        compression="gzip",
        engine="pyarrow",
    )
    logger.info(f"Запуск для файла {Path(file_path).stem}")

    rdf = pd.merge(df, bovinehd_manifest_df, left_on="SNP Name", right_on="Name")
    rdf.drop(columns=["Name"], inplace=True)

    logger.info("Создание колонки REF")
    rdf["REF"] = rdf.progress_apply(create_column_REF, axis=1)

    logger.info("Создание колонки ALT")
    rdf["ALT"] = rdf.progress_apply(create_column_ALT, axis=1)
    rdf = rdf[rdf["ALT"] != "DATA_ERROR"]
    rdf.columns = rdf.columns.str.strip().str.replace(" - ", "_").str.replace(" ", "_")

    grouped_by_sample = rdf.groupby("Sample_ID")

    logger.info("Создание .vcf файла")
    output_files = []

    for sample_id, sample_data in tqdm(
        grouped_by_sample, total=len(grouped_by_sample), disable=True
    ):
        output_files.append(
            create_vcf_for_sample(
                sample_id, sample_data, Path(file_path).name, path_to_result
            )
        )

    return {"main": output_files}


if __name__ == "__main__":
    # 1. Конфигурация ----
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.debug("Загрузка файла манифеста")
    bovinehd_manifest_df = pd.read_csv(  # pyright: ignore[reportCallIssue]
        os.getenv("MANIFEST_PATH"),
        sep=",",
        header=7,
        skipfooter=24,
        usecols=["Name", "IlmnStrand", "SNP", "RefStrand"],
        engine="python",
    )

    logger.debug("Загрузка завершена. Начинаем обработку файла")

    print(
        process_file(
            "tests/data/unpacked/test_data_test_data_res_FinalReport.txt.gz",
            "tests/results",
        )
    )

    # logger.info("Подготовка файлов...")
    # input_directory = os.getenv("PATH_TO_RAW")
    # output_directory = os.getenv("PATH_TO_PREPARED")
    # path_to_data = os.getenv("PATH_TO_PREPARED")

    # test_mode = True if os.getenv("TEST_MODE", "False") == "True" else False
    # if test_mode:
    #     input_directory = os.getenv("PATH_TO_RAW_TEST")
    #     output_directory = os.getenv("PATH_TO_PREPARED_TEST")
    #     path_to_data = os.getenv("PATH_TO_PREPARED_TEST")

    # process_archives(input_directory, output_directory)

    # all_data = os.listdir(path_to_data)
    # # [4:5] - самый маленький файл
    # # all_data = [all_data[-2]]
    # # all_data = all_data[4:5]

    # logger.info("Загрузка общего файла манифеста...")
    # bovinehd_manifest_df = pd.read_csv(  # pyright: ignore[reportCallIssue]
    #     os.getenv("MANIFEST_PATH"),
    #     sep=",",
    #     header=7,
    #     skipfooter=24,
    #     usecols=["Name", "IlmnStrand", "SNP", "RefStrand"],
    #     engine="python",
    # )

    # logger.debug(all_data)
    # logger.info("Конвертация...")
    # for file in tqdm(all_data, total=len(all_data)):
    #     process_file(file, path_to_data, bovinehd_manifest_df)

    # # Сжатие, индексирование, объединение, создания формата для plink
    # cmd = CMD()
    # cmd.prepare_vcf_files()
    # cmd.merge_vcf()
    # cmd.convert_to_plink()
