        const socket = io();
        
        socket.on('connect', () => { 
            console.log("Produção Conectada."); 
        });

        socket.on('cmd', (data) => {
            if (data.type === 'sync') {
                scrollToLine(data.index);
                return;
            }

            scrollToLine(data.index);
            
            if (data.type === 'jump') showAlert("⚠️ SALTO", "jump");
            if (data.type === 'back') showAlert("⏪ RETROCESSO", "back");
        });

        function scrollToLine(index) {
            document.querySelectorAll('.script-line').forEach(el => el.classList.remove('active'));
            const el = document.getElementById(`line-${index}`);
            if (el) {
                el.classList.add('active');
                setTimeout(() => {
                    el.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                }, 50);
            }
        }

        function showAlert(msg, type) {
            const box = document.getElementById('alert-box');
            box.innerText = msg;
            box.className = type === 'jump' ? 'alert-jump' : 'alert-back';
            box.style.display = 'block';
            setTimeout(() => { box.style.display = 'none'; }, 2000);
        }
        
        window.onload = () => scrollToLine(0);
