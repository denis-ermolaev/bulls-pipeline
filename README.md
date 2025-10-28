## Данные
Референсный геном

data/reference/ncbi_dataset/data/GCF_002263795.3/GCF_002263795.3_ARS-UCD2.0_genomic.fna

Создание индекса

`/opt/tools/samtools-1.16/samtools faidx data/reference/ncbi_dataset/data/GCF_002263795.3/GCF_002263795.3_ARS-UCD2.0_genomic.fna`

Файл манифеста (BovineHD_B1.csv) должен находиться в директории data/manifest/

Сырые данные  data/raw

## Получение нуклеотида из референса

/opt/tools/samtools-1.16/samtools faidx /home/ermolaevd/bulls-vcf-pipeline/data/reference/ncbi_dataset/data/GCF_002263795.3/GCF_002263795.3_ARS-UCD2.0_genomic.fna NC_037328.1:776231-776231

>A

/opt/tools/samtools-1.16/samtools faidx /home/ermolaevd/bulls-vcf-pipeline/data/old_reference/Bos_taurus.UMD3.1.dna.toplevel.fa 1:776231-776231

>T

## Запуск проекта
`manage_project_files.py`

Из zip архивов создаёт для файлов FinalReport архив формата .txt.gz в директории data/unpacked/

`run.py`

Результаты в data_result, в директории созданной для каждого .txt.gz архива, внутри .vcf файла для каждой коровы отдельно

Список с путями ко всем файлам
`find data_result -name '*.vcf' > vcf_file_list.txt`

while read file; do
    /opt/tools/bin/bgzip -f "$file"
done < vcf_file_list.txt

Список с путями ко всем файлам
`find data_result -name '*.vcf.gz' > vcf_file_list.txt`


while IFS= read -r vcf_file; do
  /opt/tools/bin/bcftools index "$vcf_file"
done < vcf_file_list.txt

Объединение всех vcf файлов
`/opt/tools/bin/bcftools merge -l vcf_file_list.txt -o merged.vcf`


Сжатие:
`/opt/tools/bin/bgzip result_merged.vcf`
`/opt/tools/bin/bcftools index -t result_merged.vcf.gz`

Формат пригодный для plink
`plink/plink --vcf result_merged.vcf.gz --make-bed --chr-set 31 --memory 100000 --out /home/ermolaevd/bulls-vcf-pipeline/result_plink/merged`


plink/plink \
    --bfile /home/ermolaevd/bulls-vcf-pipeline/result_plink/merged \
    --memory 100000 \
    --chr-set 31 \
    --freq \
    --out /home/ermolaevd/bulls-vcf-pipeline/analysis_results/freq_stats


plink/plink \
    --bfile /home/ermolaevd/bulls-vcf-pipeline/result_plink/merged \
    --memory 100000 \
    --chr-set 31 \
    --r2 \
    --ld-window-kb 1000 \
    --ld-window 99999 \
    --ld-window-r2 0.2 \
    --out /home/ermolaevd/bulls-vcf-pipeline/analysis_results/ld_analysis

