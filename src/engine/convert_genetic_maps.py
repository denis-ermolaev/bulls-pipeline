import csv
import os


def convert_genetic_maps(
    input: dict[str, list[str]], output_dir: str
) -> dict[str, list[str]] | None:
    """
    Конвертирует CSV с генетической картой в набор .map-файлов по хромосомам.
    Ожидается, что CSV имеет заголовок:
    Chr,Name,Mbp_position,cM_likelihood,cM_deterministic,recrate_adjacent_deterministic,Mbp_inter_marker_distance
    """
    input_file = input["main"][0]  # Берём первый, движок подразумевает 1 файл
    chromosomes = {}  # ключ: номер хромосомы, значение: список строк для .map
    seen_positions = set()  # для контроля уникальности (хромосома, bp)

    with open(input_file, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        next(reader)  # пропускаем заголовок

        for row_num, row in enumerate(reader, start=2):
            if not row or all(cell.strip() == "" for cell in row):
                continue

            # Берём нужные колонки
            chr_id = row[0].strip()
            mbp_str = row[2].strip()
            cm_str = row[3].strip()  # используем cM_likelihood

            # Замена десятичной запятой на точку
            mbp_str = mbp_str.replace(",", ".")
            cm_str = cm_str.replace(",", ".")

            try:
                mbp = float(mbp_str)  # мегабазы
                cm = float(cm_str)  # сантиморганы
            except ValueError:
                print(
                    f"Предупреждение: строка {row_num} — ошибка преобразования чисел (Mbp={mbp_str}, cM={cm_str})"
                )
                continue

            # Физическая позиция в парах оснований (bp)
            bp = int(round(mbp * 1_000_000))

            # Очень маленькие значения cM (например, 5e-17) приравниваем к нулю
            if abs(cm) < 1e-12:
                cm = 0.0

            # Формируем строку в формате .map: хромосома <пробел> . <пробел> cM <пробел> bp
            map_line = f"{chr_id}\t.\t{cm:.6f}\t{bp}"

            # Сохраняем в словарь по хромосоме
            key = (chr_id, bp)
            if key not in seen_positions:
                seen_positions.add(key)
                chromosomes.setdefault(chr_id, []).append(map_line)
            # chromosomes.setdefault(chr_id, []).append(map_line)  # закомментировано
    if not chromosomes:
        print("Не найдено ни одной корректной записи. Проверьте формат входного файла.")
        return

    # Создаём выходную директорию
    os.makedirs(output_dir, exist_ok=True)
    output: dict[str, list[str]] = {"main": []}
    # Записываем файлы для каждой хромосомы
    for chr_id, lines in chromosomes.items():
        # Имя файла: chr1.map, chr2.map, ... chrX.map и т.д.
        lines.sort(key=lambda x: int(x.split("\t")[3]))
        out_file = os.path.join(output_dir, f"chr{chr_id}.map")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        output["main"].append(out_file)
        print(f"Создан {out_file} — {len(lines)} SNP")

    return output


# if __name__ == "__main__":
