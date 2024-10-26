from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

# Kullanıcılar ve özel odalar için veri yapıları
users = {}
private_rooms = {}

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if "register" in request.form:  # Kayıt olma
            username = request.form.get("username")
            if username in users:
                return render_template("home.html", error="Kullanıcı adı zaten mevcut.")
            user_id = str(uuid.uuid4())  # Her kullanıcıya benzersiz bir ID atanıyor
            users[username] = user_id
            return render_template("home.html", success="Başarıyla kayıt oldunuz, giriş yapabilirsiniz.")
        
        elif "login" in request.form:  # Giriş yapma
            username = request.form.get("username")
            if username not in users:
                return render_template("home.html", error="Kullanıcı adı bulunamadı.")
            session["username"] = username
            session["user_id"] = users[username]
            return redirect(url_for("user_list"))

    return render_template("home.html")

@app.route("/user_list")
def user_list():
    if "username" not in session:
        return redirect(url_for("home"))
    # Diğer tüm kullanıcıları listeliyoruz, giriş yapan hariç
    other_users = {k: v for k, v in users.items() if k != session["username"]}
    return render_template("user_list.html", users=other_users, username=session["username"])

@app.route("/private_chat/<target_user>")
def private_chat(target_user):
    if "username" not in session or target_user not in users:
        return redirect(url_for("home"))

    current_user = session["username"]
    room_id = f"{session['user_id']}-{users[target_user]}" if session["user_id"] < users[target_user] else f"{users[target_user]}-{session['user_id']}"
    if room_id not in private_rooms:
        private_rooms[room_id] = {"members": [current_user, target_user], "messages": []}
    
    session["room_id"] = room_id
    return render_template("private_chat.html", room_id=room_id, messages=private_rooms[room_id]["messages"], target_user=target_user)

@socketio.on("message")
def handle_message(data):
    room_id = session.get("room_id")
    if room_id not in private_rooms:
        return

    content = {
        "name": session["username"],
        "message": data["message"]
    }
    send(content, to=room_id)
    private_rooms[room_id]["messages"].append(content)
    print(f"{session['username']} said: {data['message']} in room {room_id}")

@socketio.on("join")
def on_join(data):
    room_id = session.get("room_id")
    if not room_id:
        return
    
    join_room(room_id)
    send({"name": session["username"], "message": "has entered the chat"}, to=room_id)

@socketio.on("disconnect")
def handle_disconnect():
    room_id = session.get("room_id")
    if not room_id:
        return
    
    leave_room(room_id)
    send({"name": session["username"], "message": "has left the chat"}, to=room_id)

if __name__ == "__main__":
    socketio.run(app, debug=True)
