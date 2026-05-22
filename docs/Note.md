


/opt/tools/bin/bcftools view -r 24 /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz -Oz -o /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr1.vcf.gz

```bash
for var in list
do
команды
done
```

# Разделение на хромосомы
for (( i=1; i <= 31; i++ ))
do
echo "number is $i"
/opt/tools/bin/bcftools view -r $i /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz -Oz -o /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr${i}.vcf.gz
done


# 29 - т.к пока только для аутосом (С X может быть проблема ?)
for (( i=1; i <= 29; i++ ))
do
echo "number is $i"
mkdir -p /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr${i}
java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr${i}_phased_snp.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr${i}.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps_holstein/chr${i}.map \
    out=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr${i}/chr${i} \
    chrom=${i} \
    nthreads=16 \
    ne=50000 \
    cluster=0.005 \
    window=200 \
    em=false \
    impute=true
done


java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr17_phased_snp.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/chromosomes/chr17.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps_holstein/chr17.map \
    out=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr17/chr17 \
    chrom=17 \
    nthreads=16 \
    ne=50000 \
    cluster=0.005 \
    window=200 \
    em=false \
    impute=true


/opt/tools/bin/bcftools query -i 'DR2>0.8' -f '%CHROM\n' /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr24/chr24.vcf.gz | wc -l

# посмотреть заголовок — есть ли строка ##INFO=<ID=DR2,...>
/opt/tools/bin/bcftools view -h /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr1/chr1.vcf.gz | grep DR2

/opt/tools/bin/bcftools query -f '%INFO\n' /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr1/chr1.vcf.gz | head -1

/opt/tools/bin/bcftools query -i 'DR2>0.8' -f '%CHROM\t%POS\t%INFO/DR2\n' \
  /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr1/chr1.vcf.gz | head



# Убрать Генотипы, для более бытрого анализа по INFO, чтобы подвести статистику по DR2
```bash
for (( i=1; i <= 29; i++ ))
do
echo "number is $i"
/opt/tools/bin/bcftools index /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr${i}/chr${i}_filtered.vcf.gz
# /opt/tools/bin/bcftools view -G /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr${i}/chr${i}.vcf.gz -Oz -o /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/imputation/chr${i}/chr${i}_for_analysis.vcf.gz
done
```


for f in $(cat merge_list.txt); do
    /opt/tools/bin/bcftools view -i 'INFO/DR2>=0.8' -Oz -o "${f%.vcf.gz}_filtered.vcf.gz" "$f"
done

bin/plink/plink --bfile /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/gwas/chr24/plink_filtered_chr24 --chr-set 29 --memory 80000 --blocks no-pheno-req --out /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/gwas/chr24/snps_blocks