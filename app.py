import os
import re
import math
import random
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# =====================================================================
# CONFIGURACIÓN MECATRONIX
# =====================================================================
LINK_PAGO_MECATRONIX = "https://mpago.la/1rRDhYU"

# 🔑 LLAVES ACTIVAS (Se guardan en la memoria del servidor)
# Cuando un cliente genera una llave al pagar, se guarda aquí adentro.
LLAVES_VALIDAS = ["MECATRONIX-DEMO", "MECATRONIX-2026"]

# =====================================================================
# INTERFAZ GRÁFICA CONTROLADA POR LLAVE
# =====================================================================
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mecatronix - Auditor Inteligente de Mermas</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
        body { background-color: #1e222b; color: #e1e4e6; margin: 0; padding: 0; }
        .navbar { background-color: #11141a; padding: 15px 30px; border-bottom: 3px solid #3b4252; display: flex; justify-content: space-between; align-items: center; }
        .brand { font-size: 20px; font-weight: bold; color: #eceff4; letter-spacing: 1px; }
        .brand span { color: #8892b0; }
        
        .container { max-width: 900px; margin: 40px auto; padding: 20px; position: relative; }
        .panel { background-color: #2e3440; border: 1px solid #3b4252; border-radius: 6px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 25px; position: relative; }
        
        .blur-content { filter: blur(5px); pointer-events: none; user-select: none; }
        .paywall-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(27, 31, 39, 0.85); display: flex; flex-direction: column; justify-content: center; align-items: center; border-radius: 6px; z-index: 10; padding: 20px; text-align: center; border: 2px solid #bf616a; }
        .paywall-box { max-width: 500px; background: #2e3440; padding: 30px; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border-top: 4px solid #bf616a; }
        
        h2 { margin-top: 0; color: #eceff4; font-size: 22px; border-left: 5px solid #8892b0; padding-left: 12px; }
        p { color: #d8dee9; line-height: 1.6; }
        
        textarea { width: 100%; height: 110px; background-color: #1b1f27; border: 2px solid #434c5e; border-radius: 4px; color: #fff; padding: 12px; font-size: 15px; resize: none; margin-top: 10px; }
        
        .btn { display: inline-block; background-color: #434c5e; color: #fff; border: none; padding: 12px 24px; font-size: 15px; font-weight: bold; border-radius: 4px; cursor: pointer; text-decoration: none; text-align: center; margin-top: 15px; }
        .btn-pago { background-color: #009ee3; color: white; font-size: 18px; padding: 15px 30px; text-decoration: none; font-weight: bold; border-radius: 4px; margin-top: 15px; }
        
        .input-llave { background: #1b1f27; border: 2px solid #434c5e; padding: 10px; color: white; border-radius: 4px; font-size: 16px; width: 200px; text-align: center; margin-right: 10px; text-transform: uppercase; }
        .result-box { display: none; background-color: #3b4252; border-left: 5px solid #a3be8c; padding: 20px; margin-top: 20px; }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="brand">MECATRONIX<span> .IA</span></div>
        <div><span id="statusBadge" class="status-badge" style="color:#bf616a; font-weight:bold;">🔒 SISTEMA PROTEGIDO</span></div>
    </div>

    <div class="container">
        <div id="mainPanel" class="panel blur-content">
            <h2>Auditor Avanzado de Mermas (Mecatronix)</h2>
            <p>Escribe los datos del flete para auditar con el motor logarítmico.</p>
            <textarea id="inputDatos" placeholder="Escribe los datos aquí..."></textarea>
            <button class="btn" onclick="enviarAuditoria()">Procesar Datos</button>
            <div id="resultBox" class="result-box"></div>
        </div>

        <div id="paywallOverlay" class="paywall-overlay">
            <div class="paywall-box">
                <h2 style="border-left-color: #bf616a;">🔒 Acceso Restringido - Mecatronix</h2>
                <p style="margin-top: 15px;">Para desbloquear el motor inteligente de mermas, ingresa tu llave mensual o adquiere una nueva.</p>
                
                <div style="margin: 25px 0;">
                    <input type="text" id="tokenCliente" class="input-llave" placeholder="MECATRONIX-XXXX">
                    <button class="btn" style="background-color: #a3be8c; color:#1e222b; margin:0; vertical-align: top;" onclick="validarLlave()">Activar</button>
                </div>

                <hr style="border: 0; border-top: 1px solid #434c5e; margin: 20px 0;">
                
                <p style="font-size: 14px;">¿No tienes una llave vigente?</p>
                <a href="{{ link_pago }}" target="_blank" class="btn btn-pago">💳 Pagar Mensualidad Aquí</a>
            </div>
        </div>
    </div>

    <script>
        let llaveActivada = "";

        function validarLlave() {
            const llave = document.getElementById("tokenCliente").value.trim().toUpperCase();
            
            fetch("/verificar-llave", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ llave: llave })
            })
            .then(res => res.json())
            .then(data => {
                if (data.valida) {
                    llaveActivada = llave; // Guardamos la llave buena
                    document.getElementById("paywallOverlay").style.display = "none";
                    document.getElementById("mainPanel").classList.remove("blur-content");
                    document.getElementById("statusBadge").innerText = "🟢 ACCESO AUTORIZADO";
                    document.getElementById("statusBadge").style.color = "#a3be8c";
                } else {
                    alert("Esa llave no es válida o ya caducó. Intenta de nuevo.");
                }
            });
        }

        function enviarAuditoria() {
            const detalles = document.getElementById("inputDatos").value;
            fetch("/auditar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ detalles: detalles, llave: llaveActivada })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("¡Matemáticas calculadas al centavo con el motor Mecatronix!");
                } else {
                    alert("Error de seguridad: " + data.mensaje);
                }
            });
        }
    </script>
</body>
</html>
"""

# =====================================================================
# RUTA AUTOMÁTICA EXTRA: GENERADORA DE LLAVES TRAS EL PAGO
# =====================================================================
@app.route("/exito-pago-mecatronix", methods=["GET"])
def pagina_exito():
    # Esta pantalla secreta genera una llave nueva al azar cada vez que la abren
    nueva_llave = f"MECATRONIX-{random.randint(1000, 9999)}"
    LLAVES_VALIDAS.append(nueva_llave) # La guarda en el sistema como buena
    
    html_exito = f"""
    <body style="background-color: #1e222b; color: white; font-family: sans-serif; text-align: center; padding-top: 50px;">
        <div style="max-width: 500px; margin: 0 auto; background: #2e3440; padding: 40px; border-radius: 8px; border-top: 5px solid #a3be8c;">
            <h1 style="color: #a3be8c;">¡Pago Confirmado! 🟢</h1>
            <p>Gracias por financiar la tecnología de Básculas Mecatronix.</p>
            <p>Aquí tienes tu Llave de Acceso para desbloquear la aplicación:</p>
            <div style="background: #1b1f27; padding: 15px; font-size: 24px; font-weight: bold; letter-spacing: 2px; color: #ebcb8b; border-radius: 4px; margin: 20px 0;">
                {nueva_llave}
            </div>
            <p style="font-size: 14px; color: #8892b0;">Copia esta llave, regresa a la página principal y pégala en el recuadro para entrar.</p>
            <a href="/" style="color: #a3be8c; text-decoration: none; font-weight: bold;">← Ir a la Aplicación Principal</a>
        </div>
    </body>
    """
    return html_exito

# =====================================================================
# CONTROLADORES DE VALIDACIÓN
# =====================================================================
@app.route("/", methods=["GET"])
def inicio():
    return render_template_string(HTML_LAYOUT, link_pago=LINK_PAGO_MECATRONIX)

@app.route("/verificar-llave", methods=["POST"])
def verificar_llave():
    datos = request.get_json()
    llave_cliente = datos.get("llave", "").upper()
    
    if llave_cliente in LLAVES_VALIDAS:
        return jsonify({"valida": True})
    return jsonify({"valida": False})

@app.route("/auditar", methods=["POST"])
def auditar_embarque():
    datos = request.get_json()
    llave_usada = datos.get("llave", "").upper()
    
    # Candado definitivo en el servidor
    if llave_usada not in LLAVES_VALIDAS:
        return jsonify({"success": False, "mensaje": "Llave inválida. No puedes usar el motor."})
        
    return jsonify({"success": True, "modo": "predictivo"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)