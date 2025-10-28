import pandas as pd
import os
import tools
import pysam
from pathlib import Path

from tqdm import tqdm


tqdm.pandas()  # подключить поддержку progress_apply


path_to_data = os.path.join("data", "unpacked")
all_data = os.listdir(path_to_data)
# [4:5] - самый маленький файл
# all_data = [all_data[-2]]
# all_data = all_data[4:5]


def create_vcf_for_sample(sample_id, sample_df, name_file):
    """
    Создает VCF файл для одного образца на основе его данных в DataFrame.
    """
    filepath = f"data_result/{name_file}/{sample_id}.vcf"
    output_path = Path(f"data_result/{name_file}")

    # 3. Создаем директорию и все родительские директории, если их нет
    output_path.mkdir(parents=True, exist_ok=True)

    # Формируем полный путь к файлу

    # --- Шаг 1: Создание заголовка (Header) ---
    header = pysam.VariantHeader()

    # Добавляем информацию о хромосомах (контигах)
    # Берем уникальные хромосомы из данных этого образца
    for chrom in sample_df["Chr"].unique():
        header.add_meta("contig", items=[("ID", str(chrom))])

    # Добавляем описание полей FORMAT, которые мы будем использовать
    header.add_meta(
        "FORMAT",
        items=[
            ("ID", "GT"),
            ("Number", "1"),
            ("Type", "String"),
            ("Description", "Genotype"),
        ],
    )

    # Добавляем имя нашего образца в заголовок
    header.add_sample(sample_id)

    # --- Шаг 2: Создание VCF файла для записи ---
    vcf_out = pysam.VariantFile(filepath, "w", header=header)

    # --- Шаг 3: Итерация по SNP и создание записей ---
    for row in sample_df.itertuples():
        # Создаем новую запись. pysam использует 0-based координаты
        record = vcf_out.new_record(
            contig=str(row.Chr),
            start=row.Position,  # VCF POS (1-based) -> pysam start (0-based)
            alleles=(row.REF, row.ALT),
            id=row.SNP_Name,
        )

        record.filter.add("PASS")

        # --- Логика определения генотипа (самая важная часть) ---
        # .SNP .IlmnStrand .RefStrand .REF .ALT
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
            # Т.к неизвестно какой от Отца, а какой от матери
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
    complementarity = {"A": "T", "T": "A", "C": "G", "G": "C"}
    if pd.isnull(row["REF"]) or pd.isnull(row["SNP"]) or pd.isnull(row["RefStrand"]):
        return "DATA_ERROR"

    ref_allele = row["REF"]
    snp = row["SNP"].strip("[]").split("/")
    ref_strand = row["RefStrand"]

    if ref_strand == "+":
        if ref_allele in snp:
            return snp[0] if snp[1] == ref_allele else snp[1]
        else:
            return "DATA_ERROR"
    elif ref_strand == "-":
        # complement_ref = complementarity.get(ref_allele)
        snp = [complementarity[snp[0]], complementarity[snp[1]]]
        if ref_allele in snp:
            return snp[0] if snp[1] == ref_allele else snp[1]
            # ALT для - цепи
            # alt_on_minus_strand = snp[0] if snp[1] == complement_ref else snp[1]
            # # ALT Для + цепи
            # return complementarity.get(alt_on_minus_strand)
        else:
            return "DATA_ERROR"
    else:
        return "DATA_ERROR"


def process_file(name_file, path_to_data, bovinehd_manifest_df):
    """
    Эта функция содержит всю логику для обработки ОДНОГО файла.
    Она будет выполняться в отдельном процессе.
    """
    try:
        df = pd.read_csv(
            os.path.join(path_to_data, name_file),
            sep="\t",
            header=9,
            compression="gzip",
            engine="pyarrow",
        )
        print(f"Запуск для файла {name_file}")

        rdf = pd.merge(df, bovinehd_manifest_df, left_on="SNP Name", right_on="Name")
        rdf.drop(columns=["Name"], inplace=True)

        print("Создание колонки REF")
        rdf["REF"] = rdf.progress_apply(create_column_REF, axis=1)

        print("Создание колонки ALT")
        rdf["ALT"] = rdf.progress_apply(create_column_ALT, axis=1)
        rdf = rdf[rdf["ALT"] != "DATA_ERROR"]
        rdf.columns = (
            rdf.columns.str.strip().str.replace(" - ", "_").str.replace(" ", "_")
        )

        grouped_by_sample = rdf.groupby("Sample_ID")

        print("Создание .vcf файла")
        for sample_id, sample_data in tqdm(
            grouped_by_sample, total=len(grouped_by_sample)
        ):
            create_vcf_for_sample(sample_id, sample_data, name_file)

        return None  # Возвращаем None в случае успеха

    except Exception as e:
        # Возвращаем ошибку, чтобы увидеть ее в главном процессе
        return f"Ошибка при обработке файла {name_file}: {e}"


if __name__ == "__main__":
    print("Загрузка общего файла манифеста...")
    bovinehd_manifest_df = pd.read_csv(
        "data/manifest/BovineHD_B1.csv",
        sep=",",
        header=7,
        skipfooter=24,
        usecols=["Name", "IlmnStrand", "SNP", "RefStrand"],
        engine="python",
    )
    print(all_data)
    for file in tqdm(all_data, total=len(all_data)):
        process_file(file, path_to_data, bovinehd_manifest_df)
