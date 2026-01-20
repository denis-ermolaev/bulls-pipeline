import pandas as pd
import os
from manage_project_files import process_archives
import tools
import pysam
from pathlib import Path
from dotenv import load_dotenv

from tqdm import tqdm

import logging


logger = logging.getLogger(__name__)
tqdm.pandas()  # подключить поддержку progress_apply
load_dotenv()


def create_vcf_for_sample(sample_id, sample_df, name_file):
    """
    Создает VCF файл для одного образца(организма) на основе его данных в DataFrame.
    """
    filepath = f"{os.getenv('PATH_VCF_SEP')}/{name_file}/{sample_id}.vcf"
    output_path = Path(f"{os.getenv('PATH_VCF_SEP')}/{name_file}")

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
            start=row.Position,  # VCF POS (1-based) -> pysam start (0-based)
            alleles=(row.REF, row.ALT),
            id=row.SNP_Name,
        )

        record.filter.add("PASS")

        # --- ОПРЕДЕЛЕНИЕ ГЕНОТИПА ---
        complementarity = {"A": "T", "T": "A", "C": "G", "G": "C"}
        SNP = row.SNP.strip("[]").split("/")
        IlmnStrand = row.IlmnStrand
        RefStrand = row.RefStrand
        REF = row.REF

        if IlmnStrand == "BOT":
            SNP = SNP[::-1]
        if RefStrand == "-":
            SNP = [complementarity[SNP[0]], complementarity[SNP[1]]]
        SNP = {"A": SNP[0], "B": SNP[1]}

        if row.Allele1_AB != "-" and row.Allele2_AB != "-":
            allele1 = 0 if SNP[row.Allele1_AB] == REF else 1
            allele2 = 0 if SNP[row.Allele2_AB] == REF else 1
            # Сортируем для создания нефазированного генотипа (0/1)
            # Т.к неизвестно какой от отца, а какой от матери
            gt = tuple(sorted((allele1, allele2)))
            record.samples[sample_id]["GT"] = gt
        else:
            record.samples[sample_id]["GT"] = (None, None)

        vcf_out.write(record)

    vcf_out.close()


def create_column_REF(row):
    if row.Chr == "0" or row.Position == 0:
        return None
    return tools.get_ref_base(row.Chr, row.Position)


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


def process_file(name_file, path_to_data, bovinehd_manifest_df):
    """
    Обработка одного файла
    """
    try:
        # pyarrow с 1 минуты 25 секунд до 25 секунд
        df = pd.read_csv(
            os.path.join(path_to_data, name_file),
            sep="\t",
            header=9,
            compression="gzip",
            engine="pyarrow",
        )
        logger.info(f"Запуск для файла {name_file}")

        rdf = pd.merge(df, bovinehd_manifest_df, left_on="SNP Name", right_on="Name")
        rdf.drop(columns=["Name"], inplace=True)

        logger.info("Создание колонки REF")
        rdf["REF"] = rdf.progress_apply(create_column_REF, axis=1)

        logger.info("Создание колонки ALT")
        rdf["ALT"] = rdf.progress_apply(create_column_ALT, axis=1)
        rdf = rdf[rdf["ALT"] != "DATA_ERROR"]
        rdf.columns = (
            rdf.columns.str.strip().str.replace(" - ", "_").str.replace(" ", "_")
        )

        grouped_by_sample = rdf.groupby("Sample_ID")

        logger.info("Создание .vcf файла")
        for sample_id, sample_data in tqdm(
            grouped_by_sample, total=len(grouped_by_sample)
        ):
            create_vcf_for_sample(sample_id, sample_data, name_file)

        return None  # Возвращаем None в случае успеха

    except Exception as e:
        # Возвращаем ошибку, чтобы увидеть ее в главном процессе
        logger.error(f"Ошибка при обработке файла {name_file}: {e}")


if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    logger.info("Подготовка файлов...")
    input_directory = os.getenv("PATH_TO_RAW")
    output_directory = os.getenv("PATH_TO_PREPARED")
    process_archives(input_directory, output_directory)


    path_to_data = os.getenv("PATH_TO_PREPARED")
    all_data = os.listdir(path_to_data)
    # [4:5] - самый маленький файл
    # all_data = [all_data[-2]]
    # all_data = all_data[4:5]

    logger.info("Загрузка общего файла манифеста...")
    bovinehd_manifest_df = pd.read_csv(
        os.getenv("MANIFEST_PATH"),
        sep=",",
        header=7,
        skipfooter=24,
        usecols=["Name", "IlmnStrand", "SNP", "RefStrand"],
        engine="python",
    )

    logger.debug(all_data)
    logger.info("Конвертация...")
    for file in tqdm(all_data, total=len(all_data)):
        process_file(file, path_to_data, bovinehd_manifest_df)