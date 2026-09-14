from flask import Flask, render_template_string
import pandapower as pp
import pandapower.networks as pn

app = Flask(__name__)

@app.route('/')
def home():
    try:
        # 1. Cargar la topología estándar predefinida del sistema IEEE de 9 barras
        net = pn.case9()
        
        # 2. Ejecutar el cálculo matemático (Newton-Raphson)
        pp.runpp(net, algorithm="nr")
        
        # Mapeo de nombres del diagrama
        nombres_barras = {
            0: "Bus 1", 1: "Bus 2", 2: "Bus 3",
            3: "Bus 4", 4: "Bus 5", 5: "Bus 6",
            6: "Bus 7", 7: "Bus 8", 8: "Bus 9"
        }
        
        # 3. Construir la tabla de resultados en HTML
        filas_tabla = ""
        for idx, row in net.res_bus.iterrows():
            nombre_legible = nombres_barras.get(idx, f"Bus {idx+1}")
            base_kv = net.bus.loc[idx, "vn_kv"]
            voltaje_calculado_kv = row["vm_pu"] * base_kv
            
            filas_tabla += f"""
            <tr>
                <td><b>{nombre_legible}</b></td>
                <td>{base_kv} kV</td>
                <td style="color: #38bdf8;">{row['vm_pu']:.4f} p.u.</td>
                <td>{voltaje_calculado_kv:.2f} kV</td>
                <td>{row['va_degree']:.2f}°</td>
            </tr>
            """
            
        # Diseño visual responsivo para la página web
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Simulación Sistema 9 Barras</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; text-align: center; }}
                .container {{ max-width: 800px; margin: 0 auto; background: #1e293b; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                h1 {{ color: #38bdf8; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; border: 1px solid #334155; text-align: left; }}
                th {{ background-color: #0f172a; color: #38bdf8; }}
                tr:nth-child(even) {{ background-color: #1e293b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Resultados de Simulación: Sistema de 9 Barras</h1>
                <p>Flujo de potencia calculado exitosamente con backend matricial (Pandapower).</p>
                <table>
                    <tr>
                        <th>Nodo</th>
                        <th>Voltaje Base</th>
                        <th>Voltaje (p.u.)</th>
                        <th>Voltaje Real</th>
                        <th>Ángulo de Fase</th>
                    </tr>
                    {filas_tabla}
                </table>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template)
    except Exception as e:
        return f"Error en la simulación: {str(e)}", 500
