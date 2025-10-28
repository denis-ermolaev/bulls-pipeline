import pysam

# Путь к референсному геному
# reference_genome_path = "data/old_reference/Bos_taurus.UMD3.1.dna.toplevel.fa"

reference_genome_path = "data/reference/ncbi_dataset/data/GCF_002263795.3/GCF_002263795.3_ARS-UCD2.0_genomic.fna"
fasta_handle = pysam.FastaFile(reference_genome_path)


# Хромомосомы NCBI ARS-UCD2.0
chromosome_map = {
    "1": "NC_037328.1",
    "2": "NC_037329.1",
    "3": "NC_037330.1",
    "4": "NC_037331.1",
    "5": "NC_037332.1",
    "6": "NC_037333.1",
    "7": "NC_037334.1",
    "8": "NC_037335.1",
    "9": "NC_037336.1",
    "10": "NC_037337.1",
    "11": "NC_037338.1",
    "12": "NC_037339.1",
    "13": "NC_037340.1",
    "14": "NC_037341.1",
    "15": "NC_037342.1",
    "16": "NC_037343.1",
    "17": "NC_037344.1",
    "18": "NC_037345.1",
    "19": "NC_037346.1",
    "20": "NC_037347.1",
    "21": "NC_037348.1",
    "22": "NC_037349.1",
    "23": "NC_037350.1",
    "24": "NC_037351.1",
    "25": "NC_037352.1",
    "26": "NC_037353.1",
    "27": "NC_037354.1",
    "28": "NC_037355.1",
    "29": "NC_037356.1",
    "30": "NC_037357.1",
    "31": "NC_082638.1",
    "": "NC_006853.1",  # В данных нету
}

# Хромомосомы NCBI UMD3.1
# chromosome_map = {
#     1: 'AC_000158.1',
#     2: 'AC_000159.1',
#     3: 'AC_000160.1',
#     4: 'AC_000161.1',
#     5: 'AC_000162.1',
#     6: 'AC_000163.1',
#     7: 'AC_000164.1',
#     8: 'AC_000165.1',
#     9: 'AC_000166.1',
#     10: 'AC_000167.1',
#     11: 'AC_000168.1',
#     12: 'AC_000169.1',
#     13: 'AC_000170.1',
#     14: 'AC_000171.1',
#     15: 'AC_000172.1',
#     16: 'AC_000173.1',
#     17: 'AC_000174.1',
#     18: 'AC_000175.1',
#     19: 'AC_000176.1',
#     20: 'AC_000177.1',
#     21: 'AC_000178.1',
#     22: 'AC_000179.1',
#     23: 'AC_000180.1',
#     24: 'AC_000181.1',
#     25: 'AC_000182.1',
#     26: 'AC_000183.1',
#     27: 'AC_000184.1',
#     28: 'AC_000185.1',
#     29: 'AC_000186.1',
#     30: 'AC_000187.1'
# }


def get_ref_base(chromosome: str, position: int) -> str | None:
    position = int(position)
    chromosome = chromosome_map[str(chromosome)]

    base = fasta_handle.fetch(reference=chromosome, start=position - 1, end=position)
    return base.upper()


if __name__ == "__main__":
    print(get_ref_base("30", 118403108))
    print(get_ref_base(30, 118403108))
    print(get_ref_base(30, "118403108"))
    print(get_ref_base("30", 118403108))
