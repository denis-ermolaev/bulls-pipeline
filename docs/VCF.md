# Основные действия
## Архивирование:
```bash
/opt/tools/bin/bgzip file_name.vcf
```

## Индексация:
```bash
/opt/tools/bin/bcftools index file_name.vcf.gz

# Индексация всех файлов в папке
for file in *.vcf.gz; do
    /opt/tools/bin/bcftools index "$file"
done
```
--tbi -(*) .tbi

## Пересечение:
```bash
/opt/tools/bin/bcftools isec -n=2 -Oz -p output_dir \
    first_file_path.vcf.gz \
    second_file_path.vcf.gz
```
-n=2 - пересечение в двух файлах(Можно сделать в трёх и т.п)
-p output_dir - директория с результатом
-Oz - на выходе сжатые файлы .gz

## Просмотр + фильтрация
```bash
/opt/tools/bin/bcftools view -r 24 file_path.vcf.gz -Oz -o file_output.vcf.gz
```
-Oz - сжатый .gz
-r 24:1000-2000 - извлечь диапозон, хроммосому, точные позиции(опционально)
-R text.txt - извлечь SNP по CHROM и POS в файле
-S sample.txt - извлеч инфу по конкретным образцам
-G - убирает информацию про генотипы
-i 'DR2>0.7 && AF>0.01' - фильтрация, e - исключить

## Извлечение данных в кастомном формате
```bash
/opt/tools/bin/bcftools query -f '%CHROM\t%POS\n' > ref_positions.txt

/opt/tools/bin/bcftools query -i 'DR2>0.8' -f '%CHROM\n' ваш_файл.vcf.gz | wc -l
```
1) %CHROM, %POS, %ID, %REF, %ALT, %QUAL, %FILTER - базовые поля
2) %INFO/ИМЯ_ТЕГА - для извлечения тега
3) [\t%SAMPLE=%GT] - [] - повторить для каждого образца
4) %SAMPLE - образец, %GT - его генотип
5) Также работают -S -R из view
6) -i 'AF>0.05', -i 'GT="0/1"' - фильтрация i - включить, e - исключить
7) `/opt/tools/bin/bcftools query -l ваш_файл.vcf.gz` - вывод списка всех образцов
8) -H - не печатать заголовок

## Объединение
```bash
# Объединение разных образцов
/opt/tools/bin/bcftools merge --merge all *.vcf.gz -Oz -o merge.vcf.gz


# Объединение с исключением
find /путь/к/родительской/папке -type f -name "chr*.vcf.gz" \
  ! -name "chr1_for_analysis.vcf.gz" \
  | grep -E 'chr[0-9]+\.vcf\.gz$' > merge_list.txt

# Объединение разных SNP у тех же самых образцов
/opt/tools/bin/bcftools concat -f merge_list_filtered.txt -Oz -o result_merge_filtered_all_genome.vcf.gz
```
--write-index - автоматически создать индекс

# Сортировка
```bash
/opt/tools/bin/bcftools sort input.vcf.gz -Oz -o sorted_output.vcf.gz
```

# Дополнительные действия
```bash
# Случайно перемешать образцы
shuf all_my_samples.txt > shuffled_samples.txt
# Создание двух групп
head -n 1000 shuffled_samples.txt > group1_samples.txt
tail -n 1000 shuffled_samples.txt > group2_samples.txt
```
