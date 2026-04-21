./phase_common_static \
  --input /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr14-Run8-TAUIND-public.vcf.gz \
  --region 14 \
  --output Chr14_phased.vcf.gz \
  --thread 30


/opt/tools/bin/bcftools merge -Oz -o merged_holsteins_ref.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/chr24.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz

/opt/tools/bin/bcftools view -S /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/notebooks/cluster_0_samples.txt /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz -Oz -o cluster_0.vcf.gz

/opt/tools/bin/bcftools index cluster_0.vcf.gz


/opt/tools/bin/bcftools view -S holstein_ids.txt Chr24_phased_snp.vcf.gz -Oz -o Chr24_phased_snp_holstein_only.vcf.gz
/opt/tools/bin/bcftools index Chr24_phased_snp_holstein_only.vcf.gz


java -Xmx100g -jar beagle.22Jul22.46e.jar \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/private_pub_ref_panel/my_ref_panel_for_1300_snp.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
    out=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/private_pub_ref_panel/my_ref_panel_for_1300_snp_phased.vcf.gz \
    chrom=24 \
    nthreads=16 \
    ne=50000 \
    cluster=0.005 \
    window=200 \
    em=false \
    impute=false

java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/usa_ref_my_intersect/usa_bulls_1376_intersection.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
    out=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/usa_ref_my_intersect/usa_bulls_1376_intersection_imp \
    chrom=24 \
    nthreads=16 \
    ne=50000 \
    cluster=0.005 \
    window=200 \
    em=false \
    impute=true

java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
    out=correct_imp_2_variant \
    chrom=24 \
    nthreads=24 \
    ne=50000 \
    cluster=0.005 \
    window=200 \
    em=false \
    impute=true


java -Xmx100g -jar beagle.22Jul22.46e.jar \
  gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/isec_all/my_ref_panel/my_ref_panel_1300.vcf.gz \
  out=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/isec_all/my_ref_panel/my_ref_panel_1300_phased \
  map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
  ne=100000 \
  chrom=24 \
  em=false \
  nthreads=8


java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/1300SNP-24-test-ref-panel.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/80-SNP.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
    out=test_imputed_24_80%_1300_public_ref \
    chrom=24 \
    nthreads=16 \
    ne=100000 \
    cluster=0.001 \
    em=false \
    impute=true



java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/randomSNP.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
    out=test_imputed_24_700_ALL_public_ref \
    chrom=24 \
    nthreads=16 \
    ne=100000 \
    cluster=0.001 \
    em=false \
    impute=true


java -Xmx100g -jar beagle.22Jul22.46e.jar \
    ref=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz \
    gt=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/merged.vcf.gz \
    map=/scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/genetic_maps/chr24.map \
    out=merged__imputed \
    chrom=24 \
    nthreads=16 \
    ne=100000 \
    cluster=0.001 \
    em=false \
    impute=true


for f in *.vcf; do
    /opt/tools/bin/bgzip "$f"
    /opt/tools/bin/bcftools index "$f.gz"
done

/opt/tools/bin/bcftools merge --merge all *.vcf.gz -Oz -o for_pca.vcf.gz
zcat GSM4378544_3842.raw.vcf.gz | /opt/tools/bin/bgzip > GSM4378544_3842.raw.bgzf.vcf.gz

# Выбор чётных SNP, для теста работы импутации
/opt/tools/bin/bcftools index my_downsampled_2 976.vcf.gz
/opt/tools/bin/bcftools view -r 24 /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/isec_all/merge_for_my_ref_panel.vcf.gz -Oz -o chr24_merge_for_my_ref_panel.vcf.gz
/opt/tools/bin/bcftools view -h chr24.vcf.gz > header.txt
/opt/tools/bin/bcftools view -H chr24.vcf.gz | awk 'NR % 2 == 0' | cat header.txt - | /opt/tools/bin/bcftools view -Oz -o randomSNP.vcf.gz




/opt/tools/bin/bcftools isec -n=2 -Oz -p usa_ref_intersect \
    /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz \
    /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/usa_bulls/usa_bulls.vcf.gz



/opt/tools/bin/bcftools view -r 24 /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/merged.vcf.gz -Oz -o chr24.vcf.gz
/opt/tools/bin/bcftools index chr24.vcf.gz
/opt/tools/bin/bcftools view -r 24 /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz | \
/opt/tools/bin/bcftools query -f '%CHROM\t%POS\n' > ref_positions.txt
/opt/tools/bin/bcftools view -R ref_positions.txt usa_bulls.vcf.gz -Oz -o usa_chr24_in_ref.vcf.gz
/opt/tools/bin/bcftools index group2_samples.vcf.gz

# 1. Получаем список всех SNP на хромосоме 24
/opt/tools/bin/bcftools query -f '%CHROM\t%POS\n' study_samples_1300_snp.vcf.gz > all_snps.txt
# 2. Перемешиваем и берём первые 1500
shuf all_snps.txt | head -n 50 > random_50.txt
# 3. Извлекаем эти SNP
/opt/tools/bin/bcftools view -R random_50.txt study_samples_1300_snp.vcf.gz -Oz -o random_50.vcf.gz
# 4. Индексируем
/opt/tools/bin/bcftools index random_50.vcf.gz


/opt/tools/bin/bcftools query -l /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/isec_all/0000.vcf.gz > all_samples.txt
shuf all_my_samples.txt > shuffled_samples.txt
head -n 1000 shuffled_samples.txt > group1_samples.txt
tail -n +1001 shuffled_samples.txt | head -n 1000 > group2_samples.txt
/opt/tools/bin/bcftools view \
    -S group2_samples.txt \
    -Oz -o group2_samples.vcf.gz \
    /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/merged.vcf.gz


# Получить список всех ваших образцов
/opt/tools/bin/bcftools query -l /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz > all_my_samples.txt

# Перемешать и взять первые 3000
shuf all_my_samples.txt | head -n 2976 > my_downsampled_2976.txt

# Создать VCF только с этими 3000 образцов
/opt/tools/bin/bcftools view -S my_downsampled_2976.txt -Oz -o my_downsampled_2 976.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz

# Индексировать
/opt/tools/bin/bcftools index my_downsampled_3000.vcf.gz








# Создать файл для быстрой оценки DR2 (Удаляем генотипы)
/opt/tools/bin/bcftools view -G merged__imputed.vcf.gz -Oz -o site_summary.vcf.gz


/opt/tools/bin/bcftools index GSM4378543_3886.raw.bgzf.vcf.gz
/opt/tools/bin/bcftools isec -n=2 -c none -w1 /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/GSM4378543_3886.raw.bgzf.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/separate/thintergen_share_geno_VM2_1_FinalReport.txt.gz/HORUS003910309577.vcf.gz > intersect.vcf
# Считаем сколько SNP DR2
/opt/tools/bin/bcftools view -G -i 'DR2>0.7 && AF>0.01' site_summary.vcf.gz -H | wc -l


/opt/tools/bin/bcftools index --tbi /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/usa_bulls_1300.vcf.gz
/opt/tools/bin/bcftools index /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/correct_imp_holstein_only.vcf.gz
/opt/tools/bin/bcftools view -G -i 'DR2>0.7' /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/new/correct_imp_holstein_only.vcf.gz -H | wc -l







/opt/tools/bin/bcftools query -f '%INFO/DR2\n' new/correct_imp.vcf.gz | awk '{ sum += $1; n++ } END { if (n > 0) print "Среднее DR2:", sum / n; else print "Нет данных"; }'


/opt/tools/bin/bcftools view -S /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/notebooks/cluster_1_samples.txt /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/merged.vcf.gz -Oz -o cluster_1.vcf.gz

/opt/tools/bin/bcftools view -G -i 'DR2>0.5' test_imputed_24_700_1300_public_ref.vcf.gz -H | wc -l



# Создать vcf с двумя коровами
/opt/tools/bin/bcftools query -l merged.vcf.gz > samples.txt
shuf -n 2 samples.txt > random2.txt
/opt/tools/bin/bcftools view -S random2.txt -Oz -o two_samples_zaleski_bulls-1300.vcf.gz merged.vcf.gz
/opt/tools/bin/bcftools index two_samples_zaleski_bulls-1300.vcf.gz




/opt/tools/bin/bcftools isec -n=2 -c none -w2 HORUS_shifted_fixed.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz > common_sites.txt


bcftools isec -p output_dir -n=2 -w1 -c none file1.vcf.gz file2.vcf.gz

/opt/tools/bin/bcftools index Chr1_phased_snp.vcf.gz


/opt/tools/bin/bgzip 1300SNP-24-test-ref-panel.vcf

/opt/tools/bin/bcftools query -i 'AF>0.1' -f '%INFO/DR2\n' site_summary.vcf.gz | awk '{sum+=$1; count++} END {if (count > 0) print "Average DR2 (AF > 0.1) = ", sum/count; else print "No SNPs found"}'
# 1. Посчитать, сколько всего SNP получилось на выходе
/opt/tools/bin/bcftools view -H HORUS_test_imputed.vcf.gz | wc -l

# 2. Посчитать, сколько SNP имеют DR2 > 0.8
/opt/tools/bin/bcftools query -f '%ID %INFO/DR2\n' merged_shifted_test_imputed.vcf.gz | awk '$2 > 0.8' | wc -l


/opt/tools/bin/bcftools view --threads 16 -G -i 'DR2>0.8' site_summary.vcf.gz -H | wc -l

# 3. Создать новый отфильтрованный файл только с качественными SNP
/opt/tools/bin/bcftools filter -i 'DR2>0.7 && AF>0.01' merged__imputed.vcf.gz -Oz -o result.vcf.gz

/opt/tools/bin/bcftools view -H -i 'DR2>0.8' merged_shifted_test_imputed.vcf.gz | wc -l

# Считаем сколько SNP при 0.95
/opt/tools/bin/bcftools view -H -i 'DR2>0.95' merged_shifted_test_imputed.vcf.gz | wc -l

# Считаем сколько SNP при 0.98
/opt/tools/bin/bcftools view -H -i 'DR2>0.98' merged_shifted_test_imputed.vcf.gz | wc -l


# Сравниваем аллели в твоем VCF и референсе на общих позициях
/opt/tools/bin/bcftools isec -p check_isec /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/bin/HORUS_shifted_fixed.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz

# Посмотрим на результат сравнения (колонки REF и ALT)
head -n 20 check_isec/0000.vcf | grep -v "##" | awk '{print $1, $2, $4, $5}' > my_alleles.txt
head -n 20 check_isec/0001.vcf | grep -v "##" | awk '{print $1, $2, $4, $5}' > ref_alleles.txt
paste my_alleles.txt ref_alleles.txt

/opt/tools/bin/bcftools isec -p result_folder /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/separate/thintergen_share_geno_VM2v2_1_part_1_FinalReport.txt.gz/HORUS12AA001AHF10.vcf.gz




zcat /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/results/vcf/separate/thintergen_share_geno_VM2_1_FinalReport.txt.gz/HORUS003910309577.vcf.gz | awk 'BEGIN {OFS="\t"} {if($1 !~ /^#/) $2=$2-1; print}' | /opt/tools/bin/bgzip > HORUS_shifted_fixed.vcf.gz


/opt/tools/bin/bcftools index HORUS_shifted_fixed.vcf.gz




/opt/tools/bin/bcftools filter -i 'DR2 > 0.8' HORUS_test_imputed.vcf.gz | /opt/tools/bin/bcftools view -H | wc -l


/opt/tools/bin/bcftools filter -i 'DR2 > 0.8' -Oz -o HORUS_imputed_high_quality.vcf.gz



# Создаем папку для сравнения
mkdir -p compare_snps

# Находим общие позиции и выводим различия
/opt/tools/bin/bcftools isec -p compare_snps \
  HORUS_shifted_fixed.vcf.gz \
  /scratch/storageA/zaleski_bulls/bulls-vcf-pipeline/data/ref_panel/Chr24_phased_snp.vcf.gz


# Склеиваем колонки POS, REF и ALT из твоего файла и референса рядом
paste <(/opt/tools/bin/bcftools query -f '%POS\t%REF\t%ALT\n' compare_snps/0000.vcf) \
      <(/opt/tools/bin/bcftools query -f '%REF\t%ALT\n' compare_snps/0001.vcf) | head -n 100


