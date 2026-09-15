from flask import Flask, render_template_string, make_response
import pandapower as pp
import pandapower.networks as pn
import plotly.graph_objects as go

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # 1. Ejecutar simulación matemática con pandapower
        net = pn.case9()
        pp.runpp(net, algorithm="nr")
        
        nombres_barras = {
            0: "Bus 1", 1: "Bus 2", 2: "Bus 3",
            3: "Bus 4", 4: "Bus 5", 5: "Bus 6",
            6: "Bus 7", 7: "Bus 8", 8: "Bus 9"
        }
        
        posiciones = {
            0: (0, -3),   # Bus 1
            1: (-3, 2),   # Bus 2
            2: (3, 2),    # Bus 3
            3: (0, -1),   # Bus 4
            4: (-2, 0),   # Bus 5
            5: (2, 0),    # Bus 6
            6: (-2, 1.5), # Bus 7
            7: (0, 2.5),  # Bus 8
            8: (2, 1.5)   # Bus 9
        }
        
        fig = go.Figure()

        # 2. Dibujar líneas de transmisión y mapear flujos MW/MVar
        lineas_mapeo = [
            (3, 4, 0), (4, 6, 1), (6, 7, 2), 
            (7, 8, 3), (8, 5, 4), (5, 3, 5)
        ]
        
        for u, v, idx in lineas_mapeo:
            x0, y0 = posiciones[u]
            x1, y1 = posiciones[v]
            
            p_mw = net.res_line.loc[idx, "p_from_mw"]
            q_mvar = net.res_line.loc[idx, "q_from_mvar"]
            loading = net.res_line.loc[idx, "loading_percent"]
            
            # Línea unifilar
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines',
                line=dict(width=3, color='#475569'),
                hoverinfo='none'
            ))
            
            # Marcador central interactivo para ver valores de potencia
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            fig.add_trace(go.Scatter(
                x=[mx], y=[my],
                mode='markers',
                marker=dict(size=8, color='#38bdf8', opacity=0.8),
                hoverinfo='text',
                hovertext=f"<b>Línea {nombres_barras[u]} a {nombres_barras[v]}</b><br>Potencia Activa: {p_mw:.1f} MW<br>Potencia Reactiva: {q_mvar:.1f} MVar<br>Carga: {loading:.2f}%"
            ))

        # 3. Dibujar transformadores (Acoplamiento de generación)
        trafos_mapeo = [(0, 3), (1, 6), (2, 8)]
        for u, v in trafos_mapeo:
            fig.add_trace(go.Scatter(
                x=[posiciones[u][0], posiciones[v][0]], y=[posiciones[u][1], posiciones[v][1]],
                mode='lines',
                line=dict(width=4, color='#f59e0b', dash='dash'),
                hoverinfo='none'
            ))

        # 4. Procesar Nodos (Barras)
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
            
            node_labels.append(nombre)
            node_text.append(f"<b>{nombre}</b><br>Voltaje Base: {base_kv} kV<br>Tensión: {v_pu:.4f} p.u.<br>Voltaje Real: {v_kv:.2f} kV<br>Ángulo de Fase: {angulo:.2f}°")
            node_color.append('#ef4444' if base_kv > 20 else '#10b981')

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_labels,
            textposition="bottom center",
            font=dict(color='#f8fafc', size=11),
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(color=node_color, size=22, line=dict(width=2, color='#ffffff'), symbol='square')
        ))

        fig.update_layout(
            showlegend=False, hovermode='closest',
            margin=dict(b=20, l=10, r=10, t=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', height=550
        )
        
        grafico_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

        # 5. Generar filas de la tabla de datos
        filas_tabla = ""
        for idx, row in net.res_bus.iterrows():
            nombre_legible = nombres_barras[idx]
            base_kv = net.bus.loc[idx, "vn_kv"]
            voltaje_calculado_kv = row["vm_pu"] * base_kv
            
            filas_tabla += f"""
            <tr>
                <td><b>{nombre_legible}</b></td>
                <td>{base_kv:.1f} kV</td>
                <td style="color: #38bdf8; font-weight: bold;">{row['vm_pu']:.4f} p.u.</td>
                <td style="color: #10b981; font-weight: bold;">{voltaje_calculado_kv:.2f} kV</td>
                <td>{row['va_degree']:.2f}°</td>
            </tr>
            """

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>PowerFactory - Sistema de 9 Barras</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }}
                .wrapper {{ max-width: 1100px; margin: 0 auto; }}
                header {{ text-align: center; margin-bottom: 20px; }}
                h1 {{ color: #38bdf8; margin: 0; font-size: 26px; }}
                .card {{ background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 25px; }}
                .title {{ font-size: 16px; color: #cbd5e1; margin-bottom: 15px; border-bottom: 1px solid #334155; padding-bottom: 5px; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
                th, td {{ padding: 10px 14px; border: 1px solid #334155; text-align: left; }}
                th {{ background-color: #0f172a; color: #38bdf8; }}
                tr:nth-child(even) {{ background-color: #1e293b; }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <header>
                    <h1>Sistema de Potencia IEEE de 9 Barras</h1>
                </header>
                <div class="card">
                    <div class="title">📊 Diagrama Unifilar Interactivo (Pasa el cursor sobre los círculos celestes para ver MW y MVar)</div>
                    {grafico_html}
                </div>
                <div class="card">
                    <div class="title">📋 Tabla de Resultados de Flujo de Carga (Python + pandapower)</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Barra</th>
                                <th>Voltaje Base</th>
                                <th>Voltaje (p.u.)</th>
                                <th>Voltaje Real (kV)</th>
                                <th>Ángulo</th>
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
        response = make_response(html_template)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        return make_response(f"Error interno del flujo de potencia: {str(e)}", 500)
