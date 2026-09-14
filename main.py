import pandapower as pp
import pandapower.networks as pn

def simular_red_autonoma():
    # 1. Cargar la topología estándar predefinida del sistema IEEE de 9 barras
    net = pn.case9()
    
    print("=== CONFIGURACIÓN DE LA RED DE 9 BARRAS ===")
    print(f"Número de Barras (Nodos): {len(net.bus)}")
    print(f"Número de Líneas de Transmisión: {len(net.line)}")
    print(f"Número de Transformadores: {len(net.trafo)}")
    print(f"Número de Generadores Activos: {len(net.gen) + len(net.ext_grid)}\n")
    
    # 2. Ejecutar el cálculo matemático del flujo de carga (Newton-Raphson)
    pp.runpp(net, algorithm="nr")
    
    # Mapeo visual para relacionar los índices con los nombres del diagrama
    nombres_barras = {
        0: "Bus 1", 1: "Bus 2", 2: "Bus 3",
        3: "Bus 4", 4: "Bus 5", 5: "Bus 6",
        6: "Bus 7", 7: "Bus 8", 8: "Bus 9"
    }
    
    # 3. Desplegar los resultados de tensión en la consola
    print("=== RESULTADOS DEL FLUJO DE POTENCIA ===")
    for idx, row in net.res_bus.iterrows():
        nombre_legible = nombres_barras.get(idx, f"Bus {idx+1}")
        base_kv = net.bus.loc[idx, "vn_kv"]
        voltaje_calculado_kv = row["vm_pu"] * base_kv
        
        print(f"Nodo: {nombre_legible:<6} | Voltaje Base: {base_kv:>5} kV | Medido: {row['vm_pu']:.4f} p.u. ({voltaje_calculado_kv:.2f} kV) | Ángulo: {row['va_degree']:>6.2f}°")

if __name__ == "__main__":
    simular_red_autonoma()
