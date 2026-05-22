# Beagle - импутация
## Импутация

```bash
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
```
`ref` - референсная панель
`gt` - импутируемая панель(наши образцы)
`map` - рекомбинационная карта хромосомы
`chrom` - по какой хромосоме делается импутация
`nthreads` - кол-во потоков
`ne` -
`cluster` -
`window` -
`em` -
`impute` - произвести импутацию, false - выполняется фазирование
