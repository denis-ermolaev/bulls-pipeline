import json
import pprint
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class EnsemblRestClient(object):
    def __init__(self, server="https://rest.ensembl.org", reqs_per_sec=15):
        self.server = server
        self.reqs_per_sec = reqs_per_sec
        self.req_count = 0
        self.last_req = 0

        self.species = "bos_taurus"

    def perform_rest_action(self, endpoint, hdrs=None, params=None):
        if hdrs is None:
            hdrs = {}

        if "Content-Type" not in hdrs:
            hdrs["Content-Type"] = "application/json"

        if params:
            endpoint += "?" + urlencode(params)

        data = None

        # check if we need to rate limit ourselves
        if self.req_count >= self.reqs_per_sec:
            delta = time.time() - self.last_req
            if delta < 1:
                time.sleep(1 - delta)
            self.last_req = time.time()
            self.req_count = 0

        try:
            request = Request(self.server + endpoint, headers=hdrs)
            response = urlopen(request)
            content = response.read()
            if content:
                data = json.loads(content)
            self.req_count += 1

        except HTTPError as e:
            # check if we are being rate limited by the server
            if e.code == 429:
                if "Retry-After" in e.headers:
                    retry = e.headers["Retry-After"]
                    time.sleep(float(retry))
                    self.perform_rest_action(endpoint, hdrs, params)
            else:
                sys.stderr.write(
                    "Request failed for {0}: Status code: {1.code} Reason: {1.reason}\n".format(
                        endpoint, e
                    )
                )

        return data

    def get_variants(self, species, symbol):
        genes = self.perform_rest_action(
            endpoint="/xrefs/symbol/{0}/{1}".format(species, symbol),
            params={"object_type": "gene"},
        )
        if genes:
            stable_id = genes[0]["id"]
            variants = self.perform_rest_action(
                "/overlap/id/{0}".format(stable_id), params={"feature": "variation"}
            )
            return variants
        return None

    def get_gene_by_pos(self, snp_chr, start, end):
        species = self.species
        genes = self.perform_rest_action(
            endpoint=f"/overlap/region/{species}/{snp_chr}:{start}-{end}",
            params={"feature": "gene"},
        )
        if genes:
            return genes
        return None


def run(snp_chr, snp_pos, start, end):
    # TODO: Понять как работать с API
    # TODO: Получать гены + их информацию в каких-то пределах
    # TODO: LD-блоки, учитывать насколько нужный SNP правда может быть ассоциирован с LD блоком, в котором есть ген
    client = EnsemblRestClient()
    genes = client.get_gene_by_pos(snp_chr, start, end)
    if genes:
        # # Ближайший ген
        # closest_dist, closest_gene = distances[0]
        # Фильтруем только protein_coding
        coding_genes = [g for g in genes if g.get("biotype") == "protein_coding"]

        if coding_genes:
            # Вычисляем расстояния
            coding_distances = []
            for gene in coding_genes:
                start = gene["start"]
                end = gene["end"]
                if start <= snp_pos <= end:
                    dist = 0
                elif snp_pos < start:
                    dist = start - snp_pos
                else:
                    dist = snp_pos - end
                coding_distances.append((dist, gene))
            coding_distances.sort(key=lambda x: x[0])
            closest_coding_gene = coding_distances[0][1]
            print(
                f"Ближайший белок-кодирующий ген: {closest_coding_gene.get('external_name', 'без имени')}"
            )
            print(f"Расстояние: {coding_distances[0][0]} п.н.")
            print(f"Описание: {closest_coding_gene.get('description', 'нет описания')}")
            pprint.pprint(coding_distances)
        else:
            print("В регионе нет белок-кодирующих генов.")


if __name__ == "__main__":
    run(3, 49550821, 49520821, 49580821)
