from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()


# Attempt to connect to the database
try:
    conn = psycopg2.connect(host='localhost', database='fastapi-course', user='postgres', password='2050', cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("Successfully Connected to Database")
except Exception as error:
    print("Error: ", error)

# Database model
class Post(BaseModel):
    title: str
    content: str
    published: bool = True


@app.get("/")
def root():
    return {"message": "Welcome to my game review aggregator application."}


@app.get("/posts")
def get_posts():
    cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    print(posts)
    return {"data": posts}


@app.post("/createposts", status_code=status.HTTP_201_CREATED) # The second field sends in 201, which should be called whenever a post is created
def create_posts(post : Post):
    cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """,
                   (post.title, post.content, post.published))
    conn.commit()
    new_post = cursor.fetchone()
    return {"data": new_post}


@app.get("/posts/latest")
def get_latest_post():
    # Fetch the latest added game
    found_post = cursor.fetchone()
    return {"data": found_post}


@app.get("/posts/{id}")
def get_post(id : int, response : Response):
    # Fetch the game with corresponding ID.
    # This will overrite /posts/latest if it was placed on top, so be careful about matched input fields
    cursor.execute("""SELECT * from posts WHERE id=%s""", (str(id)))
    found_post = cursor.fetchone()
    if not found_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with ID: {id} was not found")
        # response.status_code = status.HTTP_404_NOT_FOUND # Doesn't change the return value, but the client side can see 404
        # return {"message": f"post with ID: {id} was not found"}
    return {"data": found_post}


@app.put("/posts/{id}")
def update_post(id : int, post: Post):
    # Update the game with corresponding ID.
    cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id=%s RETURNING *""",
                   (post.title, post.content, post.published, str(id)))
    found_post = cursor.fetchone()
    if found_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with ID: {id} was not found")
    conn.commit()
    return {"data": found_post}


@app.delete("/posts/{id}")
def delete_post(id : int, response : Response):
    # Delete the game with corresponding ID.
    cursor.execute("""DELETE FROM posts WHERE id = %s returning *""", (str(id)))
    found_post = cursor.fetchone()
    if (found_post == None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with ID: {id} was not found")
    conn.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Do this instead of message:, as 204 = no content returned