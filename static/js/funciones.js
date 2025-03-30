document.addEventListener("DOMContentLoaded", function () {
    const button = document.querySelector("button");
    const input = document.getElementById("preguntaInput");
    const responseBox = document.getElementById("responseBox");
    const responseText = document.getElementById("responseText");
    const hallucinationBox = document.getElementById("hallucinationBox");
    const hallucinationText = document.getElementById("hallucinationText");

    button.addEventListener("click", async function () {
      const pregunta = input.value.trim();
      if (!pregunta) {
        responseBox.style.display = "block";
        responseText.innerText = "⚠️ Por favor, ingresa una pregunta.";
        return;
      }

      responseBox.style.display = "block";
      responseText.innerText = "⏳ Buscando respuesta...";
      hallucinationBox.style.display = "none";

      try {
        const res = await fetch("/preguntar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pregunta })
        });

        const data = await res.json();
        if (data.respuesta) {
          responseText.innerText = typeof data.respuesta === "string" ? data.respuesta : JSON.stringify(data.respuesta);
          hallucinationBox.style.display = "block";
          if (data.hallucination && data.hallucination.toLowerCase() === "yes") {
            hallucinationText.innerText = "⚠️ Esta respuesta podría contener alucinaciones.";
            hallucinationBox.classList.add("warning");
            hallucinationBox.classList.remove("safe");
          } else {
            hallucinationText.innerText = "✅ Esta respuesta fue generada con confianza.";
            hallucinationBox.classList.add("safe");
            hallucinationBox.classList.remove("warning");
          }
        } else if (data.error) {
          responseText.innerText = "⚠️ Error: " + data.error;
        } else {
          responseText.innerText = "❌ Algo salió mal.";
        }
      } catch (err) {
        console.error(err);
        responseText.innerText = "❌ Error al conectar con el servidor.";
      }
    });
  });