import os
from flask import Flask,render_template, request, session, redirect, url_for, flash, Response, send_file
from io import BytesIO
from PIL import Image

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'bsl.sqlite'),
    )

    from .db import get_db

    @app.route('/')
    def main():
        return render_template('home.html')
    
    @app.route('/staff')
    def staff():
        conn = get_db()
        staff = conn.execute('SELECT * FROM staff').fetchall()
        return render_template('staff.html', staff=staff)

    @app.route('/informations')
    def info():
        return render_template('informations.html')

    @app.route('/mediass')
    def media():
        return render_template('media.html')

    @app.route('/uniforme')
    def uniforme():
        return render_template('uniforme.html')
    
    @app.route('/new_post', methods=['GET', 'POST'])
    def new_post():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        conn = get_db()
        c = conn.cursor()
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['text']
            
            conn.execute("INSERT INTO forum (title, text) VALUES (?, ?)", (title, text))
            conn.commit()
            
            return redirect(url_for('posts'))
        
        return render_template('new_post.html')

    @app.route('/posts')
    def posts():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        
        conn = get_db()
        cursor = conn.execute("SELECT * FROM forum")
        posts = cursor.fetchall()
        
        return render_template('posts.html', posts=posts)

    @app.route('/delete_post/<int:post_id>', methods=['POST', 'DELETE'])
    def delete_post(post_id):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        
        conn = get_db()
        conn.execute("DELETE FROM forum WHERE id=?", (post_id,))
        conn.commit()
    
        return redirect(url_for('posts'))

    @app.route('/upload_image', methods=['GET', 'POST'])
    def upload_image():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        
        conn = get_db()
        c = conn.cursor()
        if request.method == 'POST':
            id = request.form['id']
            titre = request.form['titre']
            for file in request.files.getlist('image'):
                image = file.read()
                c.execute("INSERT INTO images (id, image, titre) VALUES (?, ?, ?)", (id, image, titre))
            conn.commit()
            return redirect(url_for('upload_image'))
        elif request.method == 'GET':
            c.execute("SELECT DISTINCT id FROM images")
            images = c.fetchall()
            id = request.args.get('id')
            if id:
                # Delete the image(s) with the given ID
                c.execute("DELETE FROM images WHERE id = ?", (id,))
                # Update the IDs of all images with a greater ID than the deleted ID
                c.execute("UPDATE images SET id = id - 1 WHERE id > ?", (id,))
                conn.commit()
            return render_template('upload_image_with_title.html', images=images)

    @app.route('/delete_image', methods=['POST'])
    def delete_image():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        
        conn = get_db()
        c = conn.cursor()
        id = request.form['id']
        c.execute("DELETE FROM images WHERE id = ?", (id,))
        c.execute("UPDATE images SET id = id - 1 WHERE id > ?", (id,))
        conn.commit()
        return redirect(url_for('upload_image'))



    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            password = request.form['password']
            if password == 'bsl2022-2023':
                session['logged_in'] = True
                return redirect(url_for('upload_image'))
            else:
                flash('Invalid password!')
        return render_template('login.html')

    
    @app.route('/show_images/<int:id>')
    def show_images(id):
        conn = get_db()
        c = conn.cursor()
        title = c.execute("SELECT titre FROM images WHERE id=? AND titre IS NOT NULL LIMIT 1", (id,)).fetchone()
        images = c.execute("SELECT image FROM images WHERE id=?", (id,)).fetchall()
        return render_template('show_images.html', images=images, id=id, enumerate=enumerate, title=title)

    @app.route('/medias')
    def medias():
        conn = get_db()
        c = conn.cursor()
        num = c.execute("SELECT DISTINCT id FROM images").fetchall()
        images = []
        for i in num:
            image = c.execute("SELECT image FROM images WHERE id=? LIMIT 1", (i[0],)).fetchone()
            title = c.execute("SELECT titre FROM images WHERE id=? AND titre IS NOT NULL LIMIT 1", (i[0],)).fetchone()
            images.append({'id': i[0], 'image': image, 'title': title})
        images = reversed(images)
        return render_template('media.html', images=images, enumerate=enumerate, num=num)


    @app.route('/serve_image/<int:id>')
    def serve_image(id):
        conn = get_db()
        c = conn.cursor()
        image_index = request.args.get('image_index')
        image_data = c.execute("SELECT image FROM images WHERE id=?", (id,)).fetchall()[int(image_index)][0]
        image = Image.open(BytesIO(image_data))
        return serve_pil_image(image)

    def serve_pil_image(pil_img):
        img_io = BytesIO()
        pil_img.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')

    from . import db
    db.init_app(app)
    
    return app
