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

    def get_genes_info(self, gene_ids):
        """
        Получает информацию о генах по списку Ensembl ID.

        Параметры
        ----------
        gene_ids : list
            Список Ensembl ID генов (например, ['ENSBTAG00000014930', ...]).

        Возвращает
        -------
        dict
            Словарь {gene_id: информация_о_гене}.
            Если ген не найден, значение будет пустым словарём.
        """
        if not gene_ids:
            return {}

        # Ensembl POST lookup/id поддерживает до 1000 идентификаторов за раз
        # Разбиваем на батчи, если генов больше
        batch_size = 100
        all_results = {}

        for i in range(0, len(gene_ids), batch_size):
            batch = gene_ids[i : i + batch_size]

            payload = json.dumps({"ids": batch})

            # Нужно расширить метод perform_rest_action для поддержки POST с телом
            # Но в вашем текущем классе его нет, поэтому используем urllib.request напрямую
            data = self._post_lookup(payload)

            if data:
                for gene_id in batch:
                    if gene_id in data:
                        all_results[gene_id] = data[gene_id]
                    else:
                        all_results[gene_id] = {}
            else:
                for gene_id in batch:
                    all_results[gene_id] = {}

        return all_results

    def _post_lookup(self, payload):
        """
        Отправляет POST-запрос на /lookup/id.

        Параметры
        ----------
        payload : str
            JSON-строка с телом запроса.

        Возвращает
        -------
        dict или None
            Ответ API в виде словаря или None в случае ошибки.
        """
        endpoint = "/lookup/id"
        url = self.server + endpoint

        # Rate limiting
        if self.req_count >= self.reqs_per_sec:
            delta = time.time() - self.last_req
            if delta < 1:
                time.sleep(1 - delta)
            self.last_req = time.time()
            self.req_count = 0

        try:
            request = Request(
                url,
                data=payload.encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response = urlopen(request)
            content = response.read()
            self.req_count += 1
            if content:
                return json.loads(content)
        except HTTPError as e:
            if e.code == 429 and "Retry-After" in e.headers:
                retry = float(e.headers["Retry-After"])
                time.sleep(retry)
                return self._post_lookup(payload)
            else:
                sys.stderr.write(
                    "Request failed for {0}: Status code: {1.code} Reason: {1.reason}\n".format(
                        endpoint, e
                    )
                )
        return None

    def _post_lookup_symbol(self, payload):
        """
        Отправляет POST-запрос на /lookup/symbol/:species.
        Тело запроса: {"symbols": ["FOXS1", ...]}.
        Возвращает словарь {symbol: {информация о гене}} или None.
        """
        endpoint = f"/lookup/symbol/{self.species}"
        url = self.server + endpoint

        # Rate limiting (точно как в _post_lookup)
        if self.req_count >= self.reqs_per_sec:
            delta = time.time() - self.last_req
            if delta < 1:
                time.sleep(1 - delta)
            self.last_req = time.time()
            self.req_count = 0

        try:
            request = Request(
                url,
                data=payload.encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response = urlopen(request)
            content = response.read()
            self.req_count += 1
            if content:
                return json.loads(content)
        except HTTPError as e:
            if e.code == 429 and "Retry-After" in e.headers:
                retry = float(e.headers["Retry-After"])
                time.sleep(retry)
                return self._post_lookup_symbol(payload)
            else:
                sys.stderr.write(
                    "Request failed for {0}: Status code: {1.code} Reason: {1.reason}\n".format(
                        endpoint, e
                    )
                )
        return None

    def get_ensembl_ids_by_symbols(self, symbols):
        """
        Возвращает словарь {symbol: ensembl_gene_id} для заданных символов генов.
        Неизвестные символы игнорируются (в словаре отсутствуют).

        Параметры
        ----------
        symbols : list of str
            Список символов генов (например, ["FOXS1", "MYLK2", ...]).

        Возвращает
        -------
        dict
            {symbol: ensembl_id}
        """
        if not symbols:
            return {}

        # Разбиваем на батчи (API принимает до 1000 символов за раз)
        batch_size = 1000
        result = {}

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            payload = json.dumps({"symbols": batch})
            data = self._post_lookup_symbol(payload)

            if data:
                for symbol, gene_info in data.items():
                    if "id" in gene_info:
                        result[symbol] = gene_info["id"]

        return result


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


def get_gene_info_by_id(gene_ids):
    """
    gene_ids = [
        "ENSBTAG00000069793",
        "ENSBTAG00000014930",  # MYLK2
        "ENSBTAG00000009206",  # FOXS1
        "ENSBTAG00000006526",  # BCL2L1
        "ENSBTAG00000016169",  # ID1
    ]
    """
    client = EnsemblRestClient()

    genes_info = client.get_genes_info(gene_ids)

    return genes_info


if __name__ == "__main__":
    run(3, 49550821, 49520821, 49580821)
    get_gene_info_by_id(
        gene_ids=[
            "ENSBTAG00000069793",
            "ENSBTAG00000014930",  # MYLK2
            "ENSBTAG00000009206",  # FOXS1
            "ENSBTAG00000006526",  # BCL2L1
            "ENSBTAG00000016169",  # ID1
            "ENSBTAG00000007930",  # NCOA6
        ]
    )

    client = EnsemblRestClient()

    print(client.get_ensembl_ids_by_symbols(["MYLK2", "FOXS1", "NCOA6"]))
