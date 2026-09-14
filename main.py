from flask import Flask, render_template_string
import pandapower as pp
import pandapower.networks as pn
import plotly.graph_objects as go

app = Flask(__name__)

@app.route('/')
def home():
    try:
        # 1. Cargar y solucionar la red del sistema IEEE de 9 barras
        net = pn.case9()
        pp.runpp(net, algorithm="nr")
        
        # Mapeo de índices de pandapower a nombres del diagrama original
        nombres_barras = {
            0: "Bus 1", 1: "Bus 2", 2: "Bus 3",
            3: "Bus 4", 4: "Bus 5", 5: "Bus 6",
            6: "Bus 7", 7: "Bus 8", 8: "Bus 9"
        }
        
        # Coordenadas (X, Y) ajustadas para emular la geometría de PowerFactory
        posiciones = {
            0: (0, -3),   # Bus 1 (Abajo - G1)
            1: (-3, 2),   # Bus 2 (Izquierda alta - G2)
            2: (3, 2),    # Bus 3 (Derecha alta - G3)
            3: (0, -1),   # Bus 4 (Centro inferior)
            4: (-2, 0),   # Bus 5 (Izquierda media - Load A)
            5: (2, 0),    # Bus 6 (Derecha media - Load B)
            6: (-2, 1.5), # Bus 7 (Izquierda superior)
            7: (0, 2.5),  # Bus 8 (Centro superior - Load C)
            8: (2, 1.5)   # Bus 9 (Derecha superior)
        }
        
        fig = go.Figure()

        # 2. Dibujar líneas de transmisión y agregar etiquetas de potencia (MW / MVar)
        # Relaciones de las líneas en case9: (from_bus, to_bus, index_linea)
        lineas_mapeo = [
            (3, 4, 0), # Line 4-5
            (4, 6, 1), # Line 5-7
            (6, 7, 2), # Line 7-8
            (7, 8, 3), # Line 8-9
            (8, 5, 4), # Line 9-6
            (5, 3, 5)  # Line 6-4
        ]
        
        for u, v, idx in lineas_mapeo:
            x0, y0 = posiciones[u]
            x1, y1 = posiciones[v]
            
            # Obtener flujos de potencia activa (MW) y reactiva (MVar) calculados
            p_mw = net.res_line.loc[idx, "p_from_mw"]
            q_mvar = net.res_line.loc[idx, "q_from_mvar"]
            loading = net.res_line.loc[idx, "loading_percent"]
            
            # Dibujar la línea física
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines',
                line=dict(width=3, color='#64748b'),
                hoverinfo='none'
            ))
            
            # Colocar etiqueta de texto en el punto medio de la línea
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            fig.add_trace(go.Scatter(
                x=[mx], y=[my],
                mode='text',
                text=[f"{p_mw:.1f} MW<br>{q_mvar:.1f} MVar"],
                textposition="top center",
                font=dict(color='#94a3b8', size=10),
                hoverinfo='text',
                hovertext=f"Línea {nombres_barras[u]} a {nombres_barras[v]}<br>Carga: {loading:.2f}%"
            ))

        # 3. Dibujar transformadores (Conexiones de Generadores a la Red)
        trafos_mapeo = [(0, 3), (1, 6), (2, 8)]
        for u, v in trafos_mapeo:
            x0, y0 = posiciones[u]
            x1, y1 = posiciones[v]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines',
                line=dict(width=4, color='#f59e0b', dash='dot'),
                hoverinfo='none'
            ))

        # 4. Dibujar Nodos (Barras) con cuadros informativos flotantes internos
        node_x, node_y, node_text, node_color, node_labels = [], [], [], [], []
        
        for idx, row in net.res_bus.iterrows():
            x, y = posiciones[idx]
            node_x.append(x)
            node_y.append(y)
            
            nombre = nombres_barras[idx]
            base_kv = net.bus.loc[idx, "vn_kv"]
            v_pu = row['vm_pu']
            v_kv = v_pu * base_kv
            angulo = row['va_degree']
            
            # Texto visible directamente debajo del nodo
            node_labels.append(f"<b>{nombre}</b><br>{v_pu:.3f} p.u.<br>{v_kv:.1f} kV")
            
            # Cuadro completo al pasar el mouse por encima
            node_text.append(
                f"<b>{nombre}</b><br>"
                f"Voltaje Base: {base_kv} kV<br>"
                f"Voltaje: {v_pu:.4f} p.u.<br>"
                f"Voltaje Real: {v_kv:.2f} kV<br>"
                f"Ángulo de Fase: {angulo:.2f}°"
            )
            
            # El color cambia según el nivel de voltaje para simular PowerFactory
            node_color.append('#ef4444' if base_kv > 20 else '#10b981')

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_labels,
            textposition="bottom center",
            font=dict(color='#f8fafc', size=11),
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(color=node_color, size=20, line=dict(width=2, color='#ffffff'))
        ))

        # Configuración estética del lienzo del mapa unifilar
        fig.update_layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=40, l=10, r=10, t=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='#1e293b',
            plot_bgcolor='#1e293b',
            height=600
        )
        
        grafico_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

        # 5. Construcción dinámica de la Tabla de Datos de las Barras
        filas_tabla = ""
        for idx, row in net.res_bus.iterrows():
            nombre_legible = nombres_barras[idx]
            base_kv = net.bus.loc[idx, "vn_kv"]
            voltaje_calculado_kv = row["vm_pu"] * base_kv
            
            filas_tabla += f"""
            <tr>
                <td><b>{nombre_legible}</b></td>
                <td>{base_kv:.1f} kV</td>
                <td style="color: #38bdf8; font-weight: bold;">{row['vm_pu']:.4f}</td>
                <td style="color: #10b981;">{voltaje_calculado_kv:.2f} kV</td>
                <td>{row['va_degree']:.2f}°</td>
            </tr>
            """

        # Estructura del documento HTML unificado
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>PowerFactory Web Clone - 9 Buses</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px; margin: 0; }}
                .main-wrapper {{ max-width: 1100px; margin: 0 auto; }}
                header {{ text-align: center; margin-bottom: 25px; }}
                h1 {{ color: #38bdf8; margin: 0 0 5px 0; font-size: 28px; }}
                p {{ color: #94a3b8; font-size: 14px; margin: 0; }}
                .card {{ background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); margin-bottom: 30px; }}
                .card-title {{ font-size: 18px; color: #f1f5f9; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
                th, td {{ padding: 12px 16px; border: 1px solid #334155; text-align: left; }}
                th {{ background-color: #0f172a; color: #38bdf8; font-weight: 600; }}
                tr:nth-child(even) {{ background-color: #1e293b; }}
                tr:hover {{ background-color: #334155; }}
            </style>
        </head>
        <body>
            <div class="main-wrapper">
                <header>
                    <h1>Simulador Unifilar: Sistema IEEE de 9 Barras</h1>
                    <p>Réplica interactiva de flujos de potencia y tensiones inspirada en DIgSILENT PowerFactory.</p>
                </header>
                
                <div class="card">
                    <div class="card-title">📊 Diagrama de Flujo de Potencia Activa/Reactiva</div>
                    {grafico_html}
                </div>

                <div class="card">
                    <div class="card-title">📋 Tabla de Datos Físicos de las Barras (Resultados Bus)</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre de la Barra</th>
                                <th>Voltaje Base</th>
                                <th>Tensión (p.u.)</th>
                                <th>Voltaje de Operación</th>
                                <th>Ángulo de Fase</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filas_tabla}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template)
    except Exception as e:
        return f"Error en el procesamiento del flujo de carga: {str(e)}", 500
