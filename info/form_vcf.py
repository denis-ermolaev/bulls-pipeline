import pandas as pd
import pysam
from pathlib import Path

name_file = "thintergen_share_geno_VM2_1_FinalReport"
df = pd.read_csv(f"data_result/{name_file}.csv")

# data_result/thintergen_share_geno_VM2_1_FinalReport.csv


df.columns = df.columns.str.strip().str.replace(" - ", "_").str.replace(" ", "_")


def create_vcf_for_sample(sample_id, sample_df):
    """
    Создает VCF файл для одного образца на основе его данных в DataFrame.
    """
    print(f"--- Создание файла для образца: {sample_id} ---")
    filepath = f"data_result/{name_file}/{sample_id}.vcf"
    output_path = Path(f"data_result/{name_file}")

    # 3. Создаем директорию и все родительские директории, если их нет
    output_path.mkdir(parents=True, exist_ok=True)

    # Формируем полный путь к файлу

    # --- Шаг 1: Создание заголовка (Header) ---
    header = pysam.VariantHeader()

    # Добавляем информацию о хромосомах (контигах)
    # Берем уникальные хромосомы из данных этого образца
    for chrom in sample_df["Chr_x"].unique():
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
            contig=str(row.Chr_x),
            start=row.Position,  # VCF POS (1-based) -> pysam start (0-based)
            alleles=(row.REF, row.ALT),
            id=row.SNP_Name,
        )

        record.filter.add("PASS")

        # --- Логика определения генотипа (самая важная часть) ---
        # Мы предполагаем, что 'A' в колонках Allele_AB соответствует REF (аллель 0)
        # а 'B' соответствует ALT (аллель 1)
        allele1 = 0 if row.Allele1_AB == "A" else 1
        allele2 = 0 if row.Allele2_AB == "A" else 1

        # Сортируем для создания нефазированного генотипа (например, 0/1)
        gt = tuple(sorted((allele1, allele2)))

        record.samples[sample_id]["GT"] = gt

        vcf_out.write(record)

    vcf_out.close()
    print(f"Файл '{filepath}' успешно создан.")


grouped_by_sample = df.groupby("Sample_ID")

for sample_id, sample_data in grouped_by_sample:
    create_vcf_for_sample(sample_id, sample_data)
