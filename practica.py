import queue
import random
import threading
import time

NUM_DOCUMENTOS = 24
NUM_TRABAJADORES = 4
FACTOR_TIEMPO = 0.1  


def crear_documentos(n=NUM_DOCUMENTOS, semilla=42):
    """Crea una lista de documentos con id y tamaño (1 a 5)."""
    rng = random.Random(semilla)
    return [{"id": i, "tamaño": rng.randint(1, 5)} for i in range(1, n + 1)]


def llenar_cola(documentos):
    cola = queue.Queue()
    for doc in documentos:
        cola.put(doc)
    return cola


def trabajador(nombre, cola, resumen, registro, lock):
    """Ciclo del trabajador: toma documentos hasta que la cola esté vacía."""
    while True:
        try:
            doc = cola.get_nowait()
        except queue.Empty:
            break 

        time.sleep(doc["tamaño"] * FACTOR_TIEMPO) 

       
        with lock:
            resumen[nombre]["documentos"] += 1
            resumen[nombre]["tamaño_total"] += doc["tamaño"]
            registro.append((doc["id"], nombre))

        cola.task_done()


def version_concurrente(documentos):
    cola = llenar_cola(documentos)
    lock = threading.Lock()
    nombres = [f"Trabajador-{i}" for i in range(1, NUM_TRABAJADORES + 1)]
    resumen = {n: {"documentos": 0, "tamaño_total": 0} for n in nombres}
    registro = []  

    hilos = [
        threading.Thread(
            target=trabajador,
            name=n,
            args=(n, cola, resumen, registro, lock),
        )
        for n in nombres
    ]

    inicio = time.perf_counter()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    duracion = time.perf_counter() - inicio

    return resumen, registro, hilos, cola, duracion


def version_secuencial(documentos):
    cola = llenar_cola(documentos)
    procesados = 0
    inicio = time.perf_counter()
    while True:
        try:
            doc = cola.get_nowait()
        except queue.Empty:
            break
        time.sleep(doc["tamaño"] * FACTOR_TIEMPO)
        procesados += 1
    return procesados, time.perf_counter() - inicio


def main():
    documentos = crear_documentos()
    tamaño_esperado = sum(d["tamaño"] for d in documentos)

    print("=" * 60)
    print(f"Procesando {NUM_DOCUMENTOS} documentos con {NUM_TRABAJADORES} hilos")
    print("=" * 60)

    resumen, registro, hilos, cola, t_conc = version_concurrente(documentos)


    print("\nRegistro detallado (orden de finalización):")
    for id_doc, nombre in registro:
        print(f"  Documento {id_doc:2d} -> {nombre}")


    print("\nResumen por trabajador:")
    print(f"  {'Trabajador':<14}{'Documentos':>12}{'Tamaño total':>15}")
    for nombre, datos in resumen.items():
        print(f"  {nombre:<14}{datos['documentos']:>12}{datos['tamaño_total']:>15}")

    total_docs = sum(d["documentos"] for d in resumen.values())
    total_tam = sum(d["tamaño_total"] for d in resumen.values())
    print(f"  {'TOTAL':<14}{total_docs:>12}{total_tam:>15}")


    print("\nVerificaciones:")
    ids = [id_doc for id_doc, _ in registro]
    v1 = total_docs == NUM_DOCUMENTOS
    v2 = sorted(ids) == list(range(1, NUM_DOCUMENTOS + 1))  
    v3 = all(not h.is_alive() for h in hilos) and cola.empty()
    v4 = total_tam == tamaño_esperado
    print(f"  [{'OK' if v1 else 'FALLO'}] 1. Suma de documentos = {total_docs} (esperado {NUM_DOCUMENTOS})")
    print(f"  [{'OK' if v2 else 'FALLO'}] 2. Cada ID aparece exactamente una vez")
    print(f"  [{'OK' if v3 else 'FALLO'}] 3. Los {NUM_TRABAJADORES} hilos finalizaron sin bloquearse")
    print(f"  [{'OK' if v4 else 'FALLO'}] Extra: tamaño total = {total_tam} (esperado {tamaño_esperado})")


    print("\nComparación de tiempos (reto adicional):")
    procesados_seq, t_seq = version_secuencial(documentos)
    print(f"  Secuencial : {t_seq:6.2f} s ({procesados_seq} documentos)")
    print(f"  4 hilos    : {t_conc:6.2f} s ({total_docs} documentos)")
    print(f"  Aceleración: {t_seq / t_conc:6.2f}x")
    print("=" * 60)


if __name__ == "__main__":
    main()

