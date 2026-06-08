import os
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)

# =====================================================================
# CONFIGURACIÓN CRÍTICA DE MECATRONIX
# Reemplaza 'TU_LLAVE_DE_OPENAI_AQUÍ' con tu clave real de OpenAI.
# =====================================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LINK_PAGO_MECATRONIX = "https://mpago.la/1rZqpC5"

client = None

# =====================================================================
# CONTROL DE ACCESO SIMULADO
# Cambia 'activo': False a 'activo': True para probar la consola
# de inmediato sin necesidad de haber pagado la suscripción aún.
# =====================================================================
USUARIO_SITUACION = {
    "activo": True,  
    "email": "ganadero_PRO@rancho.com"
}

def calcular_merma_ganado(peso_origen, horas_viaje):
    """
    Algoritmo estándar de la industria: El ganado pierde aprox 1.2% de su peso
    por cada hora de trayecto, estabilizándose en un tope máximo del 8% de merma.
    """
    porcentaje_merma = min((horas_viaje * 1.2), 8.0)
    peso_esperado_destino = peso_origen * (1 - (porcentaje_merma / 100))
    kilos_perdidos = peso_origen - peso_esperado_destino
    
    return {
        "porcentaje": round(porcentaje_merma, 2),
        "peso_destino": int(peso_esperado_destino),
        "kilos_perdidos": int(kilos_perdidos)
    }

def interpretar_datos_ia(texto_usuario):
    """
    Versión local y gratuita: Extrae los números del mensaje del ganadero
    sin consumir créditos de OpenAI.
    """
    import re
    
    # Buscamos todos los números que vengan en el texto del ganadero
    numeros = [float(n) for n in re.findall(r'\d+\.?\d*', texto_usuario)]
    
    # Si el ganadero puso al menos dos números, asumimos que el grande es peso y el chico es tiempo
    if len(numeros) >= 2:
        peso_origen = max(numeros)
        horas_viaje = min(numeros)
        
        # Le mandamos los números a tu función de arriba para que haga el cálculo
        resultado = calcular_merma_ganado(peso_origen, horas_viaje)
        
        return {
            "activo": True,
            "kilos_origen": f"{peso_origen:,.0f}",
            "horas_camino": f"{horas_viaje}",
            "porcentaje_merma": f"{resultado['porcentaje']}",
            "kilos_merma": f"{resultado['kilos_perdidos']:,.0f}",
            "kilos_destino": f"{resultado['peso_destino']:,.0f}",
            "dictamen": "Carga auditada con éxito mediante el algoritmo de precisión de Mecatronix."
        }
    
    # Si no encuentra suficientes números, le avisa amigablemente al usuario
    return {
        "activo": True,
        "error": "El sistema no logró separar los datos. Intenta escribir el mensaje incluyendo los kilos y las horas con números claros (Ejemplo: 'Cargué 18000 kg y son 4 horas')."
    }

# =====================================================================
# RUTAS DEL SERVIDOR WEB
# =====================================================================
@app.route("/", methods=["GET"])
def inicio():
    # Renderiza la interfaz gráfica cargada abajo en este mismo archivo
    return render_template_string(HTML_LAYOUT, usuario=USUARIO_SITUACION, link_pago=LINK_PAGO_MECATRONIX)

@app.route("/auditar", methods=["POST"])
def auditar_embarque():
    # 1. Si el usuario no está activo, le pide el pago
    if not USUARIO_SITUACION["activo"]:
        return jsonify({
            "success": False, 
            "mensaje": "Acceso Restringido. Tu suscripción mensual de Mecatronix no se encuentra activa."
        })
    
    # 2. Si está activo, procesa los números gratis localmente
    try:
        datos = request.get_json()
        # Leemos 'detalles' que es el nombre exacto que manda tu JavaScript
        texto_detalles = datos.get("detalles", "")
        
        # Llamamos a nuestra función matemática local
        resultado = interpretar_datos_ia(texto_detalles)
        
        # Si la función local nos devolvió un error de texto, lo mandamos a la pantalla
        if "error" in resultado:
            return jsonify({
                "success": False,
                "mensaje": resultado["error"]
            })
            
        # Le regresamos los datos exactos que tu diseño HTML necesita para pintar la tabla
        return jsonify({
            "success": True,
            "peso_origen": resultado["kilos_origen"],
            "horas": resultado["horas_camino"],
            "reporte": {
                "porcentaje": resultado["porcentaje_merma"],
                "kilos_perdidos": resultado["kilos_merma"],
                "peso_destino": resultado["kilos_destino"]
            }
        })
        
    except Exception as e:
        print(f"Error en el servidor de Render: {e}")
        return jsonify({
            "success": False,
            "mensaje": "Ocurrió un error analítico al procesar las métricas de pesaje."
        })

# =====================================================================
# INTERFAZ GRÁFICA DEL USUARIO (HTML / CSS COMPLETO)
# Diseñado con estética industrial (placas de acero gris, detalles limpios)
# =====================================================================
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mecatronix - Auditor Inteligente de Mermas</title>
    <style>
        *, *::before, *::after { box-sizing: border-box; }
        body { background-color: #1a1d24; color: #d8dee9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; }
        
        /* Barra superior industrial */
        .navbar { background-color: #0f1115; padding: 18px 35px; border-bottom: 3px solid #2e3440; display: block; overflow: hidden; }
        .brand { float: left; font-size: 22px; font-weight: 800; color: #eceff4; letter-spacing: 1.5px; }
        .brand span { color: #81a1c1; }
        .status-container { float: right; padding-top: 4px; }
        .status-badge { padding: 6px 14px; border-radius: 3px; font-size: 12px; font-weight: bold; letter-spacing: 0.5px; }
        .badge-active { background-color: #2e3440; color: #a3be8c; border: 1px solid #a3be8c; }
        .badge-inactive { background-color: #2e3440; color: #bf616a; border: 1px solid #bf616a; }

        /* Contenedor de la aplicación */
        .container { max-width: 850px; margin: 40px auto; padding: 0 20px; display: block; }
        .panel { background-color: #232831; border: 1px solid #2e3440; border-radius: 4px; padding: 35px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); margin-bottom: 30px; display: block; }
        
        h2 { margin-top: 0; margin-bottom: 15px; color: #eceff4; font-size: 24px; font-weight: 700; border-left: 5px solid #81a1c1; padding-left: 14px; }
        p { color: #aeebec; font-size: 15px; line-height: 1.6; margin-bottom: 20px; color: #b4befe; }
        
        /* Área de captura */
        textarea { width: 100%; height: 110px; background-color: #16191f; border: 2px solid #3b4252; border-radius: 4px; color: #fff; padding: 15px; font-size: 15px; line-height: 1.5; resize: none; margin-top: 10px; }
        textarea:focus { outline: none; border-color: #81a1c1; }
        
        .btn { display: inline-block; background-color: #3b4252; color: #eceff4; border: 1px solid #4c566a; padding: 12px 28px; font-size: 15px; font-weight: bold; border-radius: 4px; cursor: pointer; text-decoration: none; text-align: center; margin-top: 15px; transition: all 0.2s; }
        .btn:hover { background-color: #434c5e; border-color: #81a1c1; }
        .btn-pay { background-color: #d08770; color: #1a1d24; width: 100%; font-size: 18px; padding: 15px; margin-top: 10px; border: none; letter-spacing: 0.5px; }
        .btn-pay:hover { background-color: #ebcb8b; }

        /* Mapeo de Resultados en Tabla */
        .result-box { display: none; background-color: #2e3440; border-left: 5px solid #a3be8c; padding: 25px; margin-top: 25px; border-radius: 0 4px 4px 0; }
        .result-table { display: table; width: 100%; margin-top: 10px; }
        .result-row { display: table-row; }
        .result-cell { display: table-cell; padding: 12px; border-bottom: 1px solid #3b4252; font-size: 15px; }
        .cell-title { font-weight: bold; color: #d8dee9; width: 45%; }
        
        .alert-danger { background-color: #bf616a; color: #eceff4; padding: 15px; border-radius: 4px; margin-top: 20px; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="brand">MECATRONIX<span> .IA</span></div>
        <div class="status-container">
            {% if usuario.activo %}
                <span class="status-badge badge-active">⚙ CONSOLA OPERATIVA</span>
            {% else %}
                <span class="status-badge badge-inactive">🔒 RESTRINGIDO</span>
            {% endif %}
        </div>
    </div>

    <div class="container">
        
        {% if not usuario.activo %}
        <div class="panel" style="border: 1px solid #d08770;">
            <h2>Activación de Licencia Requerida</h2>
            <p>Monitorea pérdidas críticas por traslado, calcula el rendimiento objetivo en destino y bloquea alteraciones maliciosas en las básculas receptoras de compradores o rastros.</p>
            <p>Habilita consultas ilimitadas para tus fletes contratando la suscripción mensual de <strong>Mecatronix Auditor</strong>.</p>
            <a href="{{ link_pago }}" class="btn btn-pay">Activar Licencia Mensual ($299 MXN)</a>
        </div>
        {% endif %}

        <div class="panel" style="opacity: {% if usuario.activo %}1{% else %}0.4{% endif %}; pointer-events: {% if usuario.activo %}auto{% else %}none{% endif %};">
            <h2>Auditoría Analítica de Carga</h2>
            <p>Describe las condiciones de tu flete usando lenguaje natural o dictándole la información directamente a la caja de texto. La Inteligencia Artificial extraerá las variables métricas.</p>
            
            <textarea id="inputDatos" placeholder="Ejemplo: Cargamos un camión con toros que dio un peso de origen en rancho de 18,500 kg y calculamos que el viaje va a demorar unas 4 horas hacia el rastro de destino..."></textarea>
            <button class="btn" onclick="ejecutarAuditoria()">Auditar Carga</button>

            <div id="errorBox" class="alert-danger" style="display: none;"></div>

            <div id="resultBox" class="result-box">
                <h3 style="margin-top:0; color: #a3be8c; letter-spacing: 0.5px;">✔ REPORTE DE AUDITORÍA COMPUTADO</h3>
                <div class="result-table">
                    <div class="result-row">
                        <div class="result-cell cell-title">Peso Origen Registrado:</div>
                        <div class="result-cell" id="resPeso">0 kg</div>
                    </div>
                    <div class="result-row">
                        <div class="result-cell cell-title">Tiempo de Tránsito Estimado:</div>
                        <div class="result-cell" id="resHoras">0 hrs</div>
                    </div>
                    <div class="result-row">
                        <div class="result-cell cell-title">Merma Esperada por Estrés:</div>
                        <div class="result-cell" id="resMerma" style="color: #d08770; font-weight: bold;">0%</div>
                    </div>
                    <div class="result-row">
                        <div class="result-cell cell-title" style="border-bottom: none;">Peso Sugerido en Destino:</div>
                        <div class="result-cell" id="resDestino" style="color: #a3be8c; font-weight: bold; font-size: 18px; border-bottom: none;">0 kg</div>
                    </div>
                </div>
                <div style="margin-top: 20px; font-size: 13.5px; color: #e5e9f0; background-color: #3b4252; padding: 15px; border-radius: 4px; border-left: 4px solid #ebcb8b; line-height: 1.5;">
                    <strong>ALERTA DE SEGURIDAD MECATRONIX:</strong> Si la báscula del comprador reporta un peso menor al Peso Sugerido en Destino, detén la descarga de inmediato. Solicita una inspección física y ajuste de calibración del equipo de pesaje receptor.
                </div>
            </div>
        </div>

    </div>

    <script>
        function ejecutarAuditoria() {
            const detalles = document.getElementById("inputDatos").value;
            const errorBox = document.getElementById("errorBox");
            const resultBox = document.getElementById("resultBox");
            
            errorBox.style.display = "none";
            resultBox.style.display = "none";

            if(!detalles.trim()) {
                errorBox.innerText = "Por favor, ingresa los detalles o descripción del flete para proceder.";
                errorBox.style.display = "block";
                return;
            }

            fetch("/auditar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ detalles: detalles })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById("resPeso").innerText = data.peso_origen.toLocaleString() + " kg";
                    document.getElementById("resHoras").innerText = data.horas + " horas";
                    document.getElementById("resMerma").innerText = data.reporte.porcentaje + " %";
                    document.getElementById("resDestino").innerText = data.reporte.peso_destino.toLocaleString() + " kg";
                    resultBox.style.display = "block";
                } else {
                    errorBox.innerText = data.mensaje;
                    errorBox.style.display = "block";
                }
            })
            .catch(() => {
                errorBox.innerText = "Falla crítica de enlace de datos con la consola Mecatronix.";
                errorBox.style.display = "block";
            });
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)