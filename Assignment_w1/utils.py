from IPython.display import HTML, display
import uuid


def show_phoenix_link(jupyter_port=8888, phoenix_port=6006):
    box_id = f"phoenix-link-box-{uuid.uuid4().hex}"
    display(HTML(f"""
    <div id="{box_id}" style="
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #f8f8f8;
        font-family: sans-serif;
    ">
      Preparing Phoenix link...
    </div>

    <script>
    (function() {{
        const current = new URL(window.location.href);
        let phoenixUrl;

        const jupyterPortPattern = "p{jupyter_port}";
        const phoenixPortPattern = "p{phoenix_port}";

        if (current.hostname.includes(jupyterPortPattern)) {{
            // DLAI-style URL:
            // s172-18-43-147p8888.lab-aws-staging.deeplearning.ai
            // ->
            // s172-18-43-147p6006.lab-aws-staging.deeplearning.ai
            const phoenixHost = current.hostname.replace(
                jupyterPortPattern,
                phoenixPortPattern
            );

            phoenixUrl = current.protocol + "//" + phoenixHost + "/";
        }} else {{
            // Fallback:
            // hostname + :6006
            //
            // Example:
            // https://some-host.example.com/notebooks/foo.ipynb
            // ->
            // https://some-host.example.com:6006/
            phoenixUrl = current.protocol + "//" + current.hostname + ":{phoenix_port}/";
        }}

        const box = document.getElementById("{box_id}");
        box.innerHTML = `
            <strong>Phoenix traces:</strong><br>
            <a href="${{phoenixUrl}}" target="_blank" rel="noopener noreferrer">
                Open Phoenix UI
            </a>
            <br>
            <small>${{phoenixUrl}}</small>
        `;
    }})();
    </script>
    """))