import gradio as gr
import edge_tts
import asyncio
import os
import io
import time

VOICES = {
    "🇺🇸 Andrew Multilingual (Podcast / Cálida)": "en-US-AndrewMultilingualNeural",
    "🇺🇸 Jenny Multilingual (Conversacional / Expresiva)": "en-US-JennyMultilingualNeural",
    "🇺🇸 Ava Multilingual (Joven / Dinámica)": "en-US-AvaMultilingualNeural",
    "🇺🇸 Brian Multilingual (Documental / Autoridad)": "en-US-BrianMultilingualNeural",
    "🇺🇸 Emma Multilingual (Audiolibros / Suave)": "en-US-EmmaMultilingualNeural",
    "🇺🇸 Guy Neural (Casual / YouTube)": "en-US-GuyNeural",
    "🇺🇸 Aria Neural (Locución de Estudio)": "en-US-AriaNeural",
    "🇲🇽 Dalia Neural (México / Expresiva)": "es-MX-DaliaNeural",
    "🇲🇽 Jorge Neural (México / Radio y Noticias)": "es-MX-JorgeNeural",
    "🇪🇸 Álvaro Neural (España / Corporativo)": "es-ES-AlvaroNeural",
    "🇪🇸 Elvira Neural (España / Narrativa)": "es-ES-ElviraNeural",
    "🇨🇴 Gonzalo Neural (Colombia / Neutro Claro)": "es-CO-GonzaloNeural",
    "🇨🇴 Salomé Neural (Colombia / Amigable)": "es-CO-SalomeNeural"
}

SPEEDS = {
    "0.8x": -20,
    "1.0x (Normal)": 0,
    "1.2x": 20,
    "1.5x": 50
}

async def core_synthesize(text, voice_id, rate_val=0, pitch_val=0, volume_val=0):
    rate_str = f"{'+' if rate_val >= 0 else ''}{rate_val}%"
    pitch_str = f"{'+' if pitch_val >= 0 else ''}{pitch_val}Hz"
    vol_str = f"{'+' if volume_val >= 0 else ''}{volume_val}%"
    
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice_id,
        rate=rate_str,
        pitch=pitch_str,
        volume=vol_str
    )
    buffer = io.BytesIO()
    async for chunk in communicator.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()

async def fn_main_editor(text, voice_label, speed_label, global_pitch, global_vol, history):
    if not text.strip():
        return None, history, "⚠️ Escribe algún texto para generar audio."
    
    voice_id = VOICES.get(voice_label, "en-US-AndrewMultilingualNeural")
    speed_val = SPEEDS.get(speed_label, 0)
    
    audio_bytes = await core_synthesize(text, voice_id, speed_val, global_pitch, global_vol)
    filename = f"audio_script_{int(time.time())}.mp3"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
        
    title = text[:35].replace("\n", " ") + "..."
    history = history or []
    history.append({"title": title, "file": filename, "voice": voice_label, "text": text})
    
    return filename, history, f"✅ Audio generado con éxito ({len(text)} caracteres)."

async def fn_podcast_studio(script, voice_a_label, voice_b_label, speed_label):
    if not script.strip():
        return None, "⚠️ El guión de podcast está vacío."
    
    voice_a = VOICES[voice_a_label]
    voice_b = VOICES[voice_b_label]
    speed_val = SPEEDS.get(speed_label, 0)
    
    lines = script.strip().split("\n")
    final_audio = io.BytesIO()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("locutor 1:") or line.lower().startswith("speaker 1:") or line.lower().startswith("host:"):
            clean_text = line.split(":", 1)[1].strip()
            chunk = await core_synthesize(clean_text, voice_a, speed_val)
            final_audio.write(chunk)
        elif line.lower().startswith("locutor 2:") or line.lower().startswith("speaker 2:") or line.lower().startswith("guest:"):
            clean_text = line.split(":", 1)[1].strip()
            chunk = await core_synthesize(clean_text, voice_b, speed_val)
            final_audio.write(chunk)
        else:
            chunk = await core_synthesize(line, voice_a, speed_val)
            final_audio.write(chunk)
            
    filename = f"podcast_{int(time.time())}.mp3"
    with open(filename, "wb") as f:
        f.write(final_audio.getvalue())
        
    return filename, "✅ Podcast generado con éxito."

async def fn_book_narration(book_text, voice_label, speed_label):
    if not book_text.strip():
        return None, "⚠️ Pega el contenido del libro."
    
    voice_id = VOICES[voice_label]
    speed_val = SPEEDS.get(speed_label, 0)
    
    paragraphs = [p.strip() for p in book_text.split("\n") if p.strip()]
    merged_audio = io.BytesIO()
    
    for p in paragraphs:
        chunk = await core_synthesize(p, voice_id, speed_val)
        merged_audio.write(chunk)
        
    filename = f"audiolibro_{int(time.time())}.mp3"
    with open(filename, "wb") as f:
        f.write(merged_audio.getvalue())
        
    return filename, f"✅ Audiolibro compilado: {len(paragraphs)} párrafos procesados."

async def fn_video_voiceover(text, voice_label, style_speed):
    if not text.strip():
        return None, None, "⚠️ Ingresa el guión para video."
    
    speed_mapping = {"⚡ Dinámico / YouTube (+15%)": 15, "🎬 Documental / Pausado (-10%)": -10, "🗣️ Comercial / Estándar (0%)": 0}
    speed_val = speed_mapping.get(style_speed, 0)
    voice_id = VOICES[voice_label]
    
    audio_bytes = await core_synthesize(text, voice_id, speed_val)
    mp3_file = f"locucion_video_{int(time.time())}.mp3"
    with open(mp3_file, "wb") as f:
        f.write(audio_bytes)
        
    srt_file = f"subtitulos_{int(time.time())}.srt"
    sentences = [s.strip() for s in text.replace(".", ".\n").split("\n") if s.strip()]
    
    srt_content = ""
    start_sec = 0.0
    for i, s in enumerate(sentences, 1):
        duration = max(2.0, len(s) * 0.065)
        end_sec = start_sec + duration
        
        def fmt_time(t):
            hrs = int(t // 3600)
            mins = int((t % 3600) // 60)
            secs = int(t % 60)
            milis = int((t - int(t)) * 1000)
            return f"{hrs:02}:{mins:02}:{secs:02},{milis:03}"
            
        srt_content += f"{i}\n{fmt_time(start_sec)} --> {fmt_time(end_sec)}\n{s}\n\n"
        start_sec = end_sec
        
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
        
    return mp3_file, srt_file, "✅ Locución y subtítulos (.SRT) generados."

custom_css = """
:root, html, body, .dark, .gradio-container, .gradio-container * {
    color-scheme: light !important;
}

body, .gradio-container {
    background-color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

footer { visibility: hidden !important; }

.app-layout {
    display: flex;
    min-height: 100vh;
    background-color: #f8fafc !important;
}

.sidebar-panel {
    width: 260px;
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
    padding: 24px 16px;
    flex-shrink: 0;
}

.brand-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-left: 6px;
}

.brand-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-weight: 800;
    font-size: 16px;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.brand-title {
    font-size: 17px;
    font-weight: 800;
    color: #0f172a !important;
    letter-spacing: -0.5px;
}

.brand-title span {
    color: #4f46e5 !important;
}

.menu-section {
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8 !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 20px 0 8px 10px;
}

.nav-btn {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: #ffffff !important;
    border: 1px solid transparent !important;
    color: #475569 !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    margin-bottom: 3px !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

.nav-btn:hover {
    background: #f1f5f9 !important;
    color: #0f172a !important;
}

.content-area {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    padding: 28px 36px;
    background-color: #f8fafc !important;
}

.card-box {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 20px;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.04) !important;
    padding: 28px 32px;
    max-width: 960px;
    margin: 0 auto;
    width: 100%;
}

.top-bar-controls {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-bottom: 18px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f1f5f9;
}

.top-bar-controls .block, .top-bar-controls select {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
}

.btn-play-hero {
    background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    max-width: 42px !important;
    aspect-ratio: 1 / 1 !important;
    padding: 0 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3) !important;
    font-size: 15px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    flex-shrink: 0 !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.btn-play-hero:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 6px 18px rgba(79, 70, 229, 0.45) !important;
    background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%) !important;
}

.custom-audio-player-top, .custom-audio-player-top .block {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
}

.clean-editor textarea {
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    background-color: #ffffff !important;
    font-size: 15.5px !important;
    line-height: 1.6 !important;
    color: #0f172a !important;
    padding: 16px !important;
    resize: none !important;
}

.clean-editor textarea:focus {
    border-color: #4f46e5 !important;
    outline: none !important;
}

.template-pill {
    border: 1px solid #e2e8f0 !important;
    background-color: #f8fafc !important;
    border-radius: 20px !important;
    padding: 6px 14px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #475569 !important;
}
"""

with gr.Blocks(title="Text to Speech Pro Studio", css=custom_css) as demo:
    
    project_history = gr.State([])
    pref_pitch = gr.State(0)
    pref_volume = gr.State(0)
    
    with gr.Row(elem_classes=["app-layout"]):
        
        with gr.Column(elem_classes=["sidebar-panel"], scale=0, min_width=260):
            gr.HTML("""
                <div class="brand-header">
                    <div class="brand-icon">⚡</div>
                    <div class="brand-title">Text to Speech <span>Pro</span></div>
                </div>
            """)
            
            btn_nav_editor = gr.Button("📝 Nuevo Guión", elem_classes=["nav-btn"])
            btn_nav_projects = gr.Button("📂 Mis Proyectos", elem_classes=["nav-btn"])
            btn_nav_voices = gr.Button("🎙️ Voces Neuronales", elem_classes=["nav-btn"])
            
            gr.HTML('<div class="menu-section">Creación Rápida</div>')
            btn_nav_podcast = gr.Button("🎧 Podcast Studio (2 Voces)", elem_classes=["nav-btn"])
            btn_nav_book = gr.Button("📖 Narración de Libros", elem_classes=["nav-btn"])
            btn_nav_video = gr.Button("🎬 Locución para Video", elem_classes=["nav-btn"])
            
            gr.HTML('<div class="menu-section">Exportación & Ajustes</div>')
            btn_nav_downloads = gr.Button("📥 Descargar MP3", elem_classes=["nav-btn"])
            btn_nav_settings = gr.Button("⚙️ Preferencias", elem_classes=["nav-btn"])

        with gr.Column(elem_classes=["content-area"]):
            
            with gr.Column(visible=True, elem_classes=["card-box"]) as view_editor:
                gr.Markdown("### 📝 Editor de Guión")
                
                with gr.Row(elem_classes=["top-bar-controls"]):
                    main_voice = gr.Dropdown(choices=list(VOICES.keys()), value="🇺🇸 Andrew Multilingual (Podcast / Cálida)", show_label=False, scale=3)
                    main_play_btn = gr.Button("▶", elem_classes=["btn-play-hero"])
                    main_speed = gr.Dropdown(choices=list(SPEEDS.keys()), value="1.0x (Normal)", show_label=False, scale=1)
                
                main_audio = gr.Audio(show_label=False, elem_classes=["custom-audio-player-top"])
                main_status = gr.Markdown("")
                
                main_text = gr.Textbox(
                    placeholder="Escribe o pega aquí tu guión...",
                    show_label=False,
                    lines=8,
                    value="Welcome to Text to Speech Pro. This platform converts your text into ultra-realistic, studio-quality speech using advanced deep learning models. Click Play and listen to the natural human inflection.",
                    elem_classes=["clean-editor"]
                )
                
                with gr.Row():
                    t1 = gr.Button("📖 Historia en Inglés", elem_classes=["template-pill"])
                    t2 = gr.Button("🎙️ Intro Podcast", elem_classes=["template-pill"])
                    t3 = gr.Button("🇲🇽 Narración Español", elem_classes=["template-pill"])

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_projects:
                gr.Markdown("### 📂 Mis Proyectos Guardados")
                projects_list = gr.Dataframe(headers=["Título", "Voz", "Archivo"], datatype=["str", "str", "str"], interactive=False)
                btn_refresh_projects = gr.Button("🔄 Actualizar Lista de Proyectos", variant="secondary")

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_voices:
                gr.Markdown("### 🎙️ Catálogo de Voces Neuronales HD")
                with gr.Row():
                    sample_voice = gr.Dropdown(choices=list(VOICES.keys()), value="🇺🇸 Jenny Multilingual (Conversacional / Expresiva)", label="Seleccionar Voz")
                    btn_test_voice = gr.Button("🔊 Escuchar Muestra", variant="primary")
                sample_audio = gr.Audio(show_label=False)

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_podcast:
                gr.Markdown("### 🎧 Podcast Studio (Multi-Voz)")
                with gr.Row():
                    pod_v1 = gr.Dropdown(choices=list(VOICES.keys()), value="🇺🇸 Andrew Multilingual (Podcast / Cálida)", label="Locutor 1 (Host)")
                    pod_v2 = gr.Dropdown(choices=list(VOICES.keys()), value="🇺🇸 Jenny Multilingual (Conversacional / Expresiva)", label="Locutor 2 (Invitado)")
                    pod_spd = gr.Dropdown(choices=list(SPEEDS.keys()), value="1.0x (Normal)", label="Velocidad")
                
                pod_audio = gr.Audio(show_label=False, elem_classes=["custom-audio-player-top"])
                pod_status = gr.Markdown("")
                
                pod_text = gr.Textbox(
                    label="Guión de Podcast (Usa 'Locutor 1:' y 'Locutor 2:')",
                    lines=8,
                    value="Locutor 1: Welcome everyone to today's tech episode!\nLocutor 2: Thanks for having me Andrew! Today we are discussing neural speech models.\nLocutor 1: Exactly, and the results are truly astonishing."
                )
                btn_gen_podcast = gr.Button("✨ Compilar Podcast Multi-Voz", variant="primary")

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_book:
                gr.Markdown("### 📖 Narración de Libros y Textos Extensos")
                with gr.Row():
                    book_voice = gr.Dropdown(choices=list(VOICES.keys()), value="🇪🇸 Elvira Neural (España / Narrativa)", label="Voz de Narrador")
                    book_speed = gr.Dropdown(choices=list(SPEEDS.keys()), value="1.0x (Normal)", label="Velocidad")
                
                book_audio = gr.Audio(show_label=False, elem_classes=["custom-audio-player-top"])
                book_status = gr.Markdown("")
                
                book_text = gr.Textbox(label="Contenido del Libro", lines=10, placeholder="Pega aquí capítulos completos...")
                btn_gen_book = gr.Button("📚 Generar Audiolibro", variant="primary")

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_video:
                gr.Markdown("### 🎬 Locución para Video & Creadores")
                with gr.Row():
                    vid_voice = gr.Dropdown(choices=list(VOICES.keys()), value="🇺🇸 Guy Neural (Casual / YouTube)", label="Voz de Locución")
                    vid_style = gr.Dropdown(choices=["⚡ Dinámico / YouTube (+15%)", "🗣️ Comercial / Estándar (0%)", "🎬 Documental / Pausado (-10%)"], value="⚡ Dinámico / YouTube (+15%)", label="Estilo de Locución")
                
                with gr.Row():
                    vid_audio = gr.Audio(label="Audio MP3", show_label=True)
                    vid_srt = gr.File(label="Subtítulos .SRT")
                vid_status = gr.Markdown("")
                
                vid_text = gr.Textbox(label="Guión del Video", lines=6, value="In this video, I will show you how to generate realistic neural voiceovers in seconds. Make sure to hit that subscribe button!")
                btn_gen_video = gr.Button("🎬 Generar Locución y Subtítulos .SRT", variant="primary")

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_downloads:
                gr.Markdown("### 📥 Centro de Exportación")
                dl_files = gr.File(label="Archivos de Audio Generados", file_count="multiple", interactive=False)
                btn_refresh_dl = gr.Button("🔄 Actualizar Archivos", variant="secondary")

            with gr.Column(visible=False, elem_classes=["card-box"]) as view_settings:
                gr.Markdown("### ⚙️ Preferencias y Calidad de Audio")
                set_pitch = gr.Slider(minimum=-30, maximum=30, value=0, step=2, label="Modulación Global de Tono (Hz)")
                set_volume = gr.Slider(minimum=-50, maximum=50, value=0, step=5, label="Ganancia de Volumen (%)")
                btn_save_settings = gr.Button("💾 Guardar Preferencias", variant="primary")
                set_status = gr.Markdown("")

    all_views = [view_editor, view_projects, view_voices, view_podcast, view_book, view_video, view_downloads, view_settings]
    
    def switch_tab(target_idx):
        return [gr.update(visible=(i == target_idx)) for i in range(len(all_views))]
    
    btn_nav_editor.click(fn=lambda: switch_tab(0), outputs=all_views)
    btn_nav_projects.click(fn=lambda: switch_tab(1), outputs=all_views)
    btn_nav_voices.click(fn=lambda: switch_tab(2), outputs=all_views)
    btn_nav_podcast.click(fn=lambda: switch_tab(3), outputs=all_views)
    btn_nav_book.click(fn=lambda: switch_tab(4), outputs=all_views)
    btn_nav_video.click(fn=lambda: switch_tab(5), outputs=all_views)
    btn_nav_downloads.click(fn=lambda: switch_tab(6), outputs=all_views)
    btn_nav_settings.click(fn=lambda: switch_tab(7), outputs=all_views)

    main_play_btn.click(
        fn=fn_main_editor,
        inputs=[main_text, main_voice, main_speed, pref_pitch, pref_volume, project_history],
        outputs=[main_audio, project_history, main_status]
    )
    t1.click(fn=lambda: "The ancient lighthouse stood firm against the midnight storm, its radiant beam piercing the dense ocean fog to guide ships safely to harbor.", outputs=main_text)
    t2.click(fn=lambda: "Hey everyone, welcome back to the channel! Today we are exploring the future of generative AI and neural voice synthesis.", outputs=main_text)
    t3.click(fn=lambda: "Bienvenidos a Text to Speech Pro. Transforma cualquier texto en locuciones claras y fluidas con entonación humana natural.", outputs=main_text)

    def update_projects(history):
        return [[p["title"], p["voice"], p["file"]] for p in (history or [])]
    btn_refresh_projects.click(fn=update_projects, inputs=[project_history], outputs=projects_list)

    btn_test_voice.click(
        fn=lambda v: fn_main_editor("Hello! This is a test sample demonstrating the natural human inflection of this voice.", v, "1.0x (Normal)", 0, 0, [])[0],
        inputs=sample_voice,
        outputs=sample_audio
    )

    btn_gen_podcast.click(fn=fn_podcast_studio, inputs=[pod_text, pod_v1, pod_v2, pod_spd], outputs=[pod_audio, pod_status])
    btn_gen_book.click(fn=fn_book_narration, inputs=[book_text, book_voice, book_speed], outputs=[book_audio, book_status])
    btn_gen_video.click(fn=fn_video_voiceover, inputs=[vid_text, vid_voice, vid_style], outputs=[vid_audio, vid_srt, vid_status])

    def get_generated_files():
        return [f for f in os.listdir(".") if f.endswith(".mp3") or f.endswith(".srt")]
    btn_refresh_dl.click(fn=get_generated_files, outputs=dl_files)

    btn_save_settings.click(fn=lambda p, v: (p, v, "✅ Preferencias guardadas correctamente."), inputs=[set_pitch, set_volume], outputs=[pref_pitch, pref_volume, set_status])

if __name__ == "__main__":
    # Render asigna el puerto 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    demo.launch(server_name="0.0.0.0", server_port=port)
