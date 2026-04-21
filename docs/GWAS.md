# PLINK

## Архив команды с пояснением


## Чистый запуск


/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --bfile merged_plink --freq --out allele_freq --chr-set 31 --memory 80000
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --bfile merged_plink --hardy --out hwe --chr-set 31 --memory 80000
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --bfile merged_plink --freqx --out freqx --chr-set 31 --memory 80000

/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --vcf two_samples_zaleski_bulls-1300.vcf.gz --make-bed --out plink_two_samples_zaleski_bulls-1300 --cow --memory 8000

/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --bfile plink_two_samples_zaleski_bulls-1300 --hardy --out zaleski_bulls-1300 --cow --memory 8000


/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --vcf two_samples_usa_bulls-1300.vcf.gz --make-bed --out plink_two_samples_usa_bulls-1300 --cow --memory 8000 --double-id 

/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink --bfile plink_two_samples_usa_bulls-1300 --hardy --out usa_bulls-1300 --cow --memory 8000


/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
  --chr-set 31 \
  --make-bed \
  --memory 80000 \
  --out /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/for_pca/merged_plink \
  --vcf /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/for_pca/merged.vcf.gz


/opt/tools/bin/bcftools isec -p intersect_dir -n=2 /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/merged.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz



/opt/tools/bin/bcftools merge -Oz -o merged_holsteins_ref.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/intersect_dir/0000.vcf //scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/intersect_dir/0001.vcf


# Перейти в директорию с файлами (или указать полные пути)
cd /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/pca/intersect_dir/

# Сжать файлы
/opt/tools/bin/bgzip 0000.vcf
/opt/tools/bin/bgzip 0001.vcf

# Индексировать
/opt/tools/bin/tabix -p vcf 0000.vcf.gz
/opt/tools/bin/tabix -p vcf 0001.vcf.gz

# Теперь merge должен работать
/opt/tools/bin/bcftools merge -Oz -o merged_holsteins_ref.vcf.gz 0000.vcf.gz 0001.vcf.gz

```bash
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
    --bfile /home/ermolaevd/bulls-vcf-pipeline/result_plink/merged \
    --memory 5000 \
    --cow \
    --freq \
    --out /home/ermolaevd/bulls-vcf-pipeline/analysis_results/freq_stats
```
Проверка качества
Колонка,Описание
CHR,Номер хромосомы.
SNP,Название (ID) маркера.
A1,"Минорный аллель (тот, что встречается реже)."
A2,"Мажорный аллель (тот, что встречается чаще)."
MAF,"Minor Allele Frequency — собственно, частота минорного аллеля (число от 0 до 0.5)."
NCHROBS,"Количество «прочитанных» хромосом (2 × количество быков, у которых этот SNP успешно отсеквенирован)."


```bash
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
    --bfile /home/ermolaevd/bulls-vcf-pipeline/result_plink/merged \
    --memory 5000 \
    --chr-set 31 \
    --r2 \
    --ld-window-kb 1000 \
    --ld-window 99999 \
    --ld-window-r2 0.2 \
    --out /home/ermolaevd/bulls-vcf-pipeline/analysis_results/ld_analysis
```
расчет Linkage Disequilibrium (LD)



```bash
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
  --bfile clean_bulls \
  --memory 5000 \
  --cow \
  --indep-pairwise 50 5 0.2 \
  --out prunning_list
```
LD Pruning (прореживание данных по сцеплению), выкидывает SNP, чтобы хорошо сработал PCA

```bash
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
  --bfile merged_plink \
  --memory 5000 \
  --cow \
  --maf 0.1 \
  --geno 0.1 \
  --mind 0.1 \
  --make-bed \
  --out clean_bulls
```
фильтр грубой очистки (Quality Control)

maf 0.1 - Популяция слишком уж консангвинная

hwe 1e-6 - убираем, т.к у нас популяция под отбором и не случано скрещивается

```bash
/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
  --bfile clean_bulls \
  --memory 5000 \
  --cow \
  --extract prunning_list.prune.in \
  --pca 10 \
  --out bulls_pca
```
PCA


/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/plink/plink \
  --bfile clean_bulls \
  --memory 5000 \
  --cow \
  --pheno pheno.txt \
  --all-pheno \
  --allow-no-sex \
  --linear \
  --covar bulls_pca.eigenvec \
  --hide-covar \
  --out gwas_results_final




/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/regenie_v4.1.gz_x86_64_Linux_mkl \
  --step 1 \
  --bed clean_bulls \
  --phenoFile pheno.txt \
  --covarFile covariates.txt \
  --nauto 29 \
  --bsize 1000 \
  --lowmem \
  --out step1_results

/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/regenie_v4.1.gz_x86_64_Linux_mkl \
  --step 2 \
  --bed clean_bulls \
  --phenoFile pheno.txt \
  --covarFile covariates.txt \
  --nauto 29 \
  --pred step1_results_pred.list \
  --bsize 400 \
  --out final_gwas_results