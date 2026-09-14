from flask import Flask, render_template_string
import pandapower as pp
import pandapower.networks as pn
import plotly.graph_objects as go

app = Flask(__name__)

@app.route('/')
def home():
    try:
        # 1. Cargar y resolver la red IEEE de 9 barras
        net = pn.case9()
        pp.runpp(net, algorithm="nr")
        
        # Mapeo de nombres originales del diagrama
        nombres_barras = {
            0: "Bus 1", 1: "Bus 2", 2: "Bus 3",
            3: "Bus 4", 4: "Bus 5", 5: "Bus 6",
            6: "Bus 7", 7: "Bus 8", 8: "Bus 9"
        }
        
        # Coordenadas aproximadas (X, Y) para replicar la geometría visual del diagrama original
        posiciones = {
            0: (0, -2),   # Bus 1 (Abajo - Generador 1)
            1: (-2.5, 2), # Bus 2 (Izquierda alta - Generador 2)
            2: (2.5, 2),  # Bus 3 (Derecha alta - Generador 3)
            3: (0, -1),   # Bus 4 (Centro inferior)
            4: (-1.5, 0), # Bus 5 (Izquierda media)
            5: (1.5, 0),  # Bus 6 (Derecha media)
            6: (-1.5, 1.5),# Bus 7 (Izquierda superior)
            7: (0, 2.5),  # Bus 8 (Centro superior)
            8: (1.5, 1.5) # Bus 9 (Derecha superior)
        }
        
        # 2. Construir las líneas de transmisión en Plotly
        edge_x = []
        edge_y = []
        
        # Conexiones explícitas basadas en la topología estándar del caso de 9 barras
        conexiones = [(3,4), (3,5), (4,6), (5,8), (6,7), (7,8)]
        for u, v in conexiones:
            x0, y0 = posiciones[u]
            x1, y1 = posiciones[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        # Conexiones de transformadores (Generadores a la red principal)
        trafos = [(0,3), (1,6), (2,8)]
        for u, v in trafos:
            x0, y0 = posiciones[u]
            x1, y1 = posiciones[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        lineas_red = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=3, color='#64748b'),
            hoverinfo='none',
            mode='lines'
        )

        # 3. Construir los nodos (Barras) con sus datos reales de la simulación
        node_x = []
        node_y = []
        node_text = []
        node_color = []

        for idx, row in net.res_bus.iterrows():
            x, y = posiciones[idx]
            node_x.append(x)
            node_y.append(y)
            
            nombre = nombres_barras.get(idx, f"Bus {idx+1}")
            base_kv = net.bus.loc[idx, "vn_kv"]
            v_pu = row['vm_pu']
            v_kv = v_pu * base_kv
            angulo = row['va_degree']
            
            # Texto informativo que saldrá al pasar el mouse por encima
            node_text.append(
                f"<b>{nombre}</b><br>"
                f"Voltaje Base: {base_kv} kV<br>"
                f"Tensión: {v_pu:.4f} p.u.<br>"
                f"Voltaje Real: {v_kv:.2f} kV<br>"
                f"Ángulo: {angulo:.2f}°"
            )
            
            # Cambiar de color los nodos según su nivel de tensión base (230kV vs Generación)
            if base_kv > 20:
                node_color.append('#ef4444') # Rojo para transmisión alta (230 kV)
            else:
                node_color.append('#10b981') # Verde/Azul para generación

        nodos_red = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[nombres_barras[i] for i in range(9)],
            textposition="top center",
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(
                showscale=False,
                color=node_color,
                size=24,
                line=dict(width=3, color='#ffffff')
            )
        )

        # 4. Crear la figura completa
        fig = go.Figure(data=[lineas_red, nodos_red],
                     layout=go.Layout(
                        title=dict(text='Diagrama Interactivo Unifilar (IEEE 9 Barras)', font=dict(color='#f8fafc', size=20)),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=60),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        paper_bgcolor='#0f172a',
                        plot_bgcolor='#0f172a'
                     )
        )

        # Convertir el gráfico interactivo a HTML puro para incrustarlo
        grafico_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

        # Diseño estructural de la interfaz de usuario
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Prototipo 9 Barras</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: #1e293b; padding: 20px; border-radius: 8px; }}
                h1 {{ color: #38bdf8; margin-bottom: 5px; }}
                p {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
                .leyenda {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 15px; font-size: 12px; }}
                .item {{ display: flex; align-items: center; gap: 5px; }}
                .color-box {{ width: 12px; height: 12px; border-radius: 50%; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Sistema de Potencia de 9 Barras</h1>
                <p>Pasa el cursor sobre los nodos para inspeccionar voltajes (p.u., kV) y ángulos calculados.</p>
                <div class="leyenda">
                    <div class="item"><div class="color-box" style="background: #ef4444;"></div> Red de Transmisión (230 kV)</div>
                    <div class="item"><div class="color-box" style="background: #10b981;"></div> Barras de Generación</div>
                </div>
                {grafico_html}
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template)
    except Exception as e:
        return f"Error en la simulación: {str(e)}", 500
