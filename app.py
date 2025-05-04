import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.environ.get("OPENAI_API_KEY")
CURRENTSAPI_KEY = os.environ.get("CURRENTSAPI_KEY")

if not openai.api_key:
    raise ValueError("Переменная окружения OPENAI_API_KEY не установлена")
if not CURRENTSAPI_KEY:
    raise ValueError("Переменная окружения CURRENTSAPI_KEY не установлена")


class Topic(BaseModel):
    topic: str


# Функция для получения последних новостей на заданную тему
def get_recent_news(topic: str):
    url = "https://api.currentsapi.services/v1/latest-news"  # URL API для получения новостей
    params = {
        "language": "en",  # Задаем язык новостей
        "keywords": topic,  # Ключевые слова для поиска новостей
        "apiKey": CURRENTSAPI_KEY  # Передаем API ключ
    }
    response = requests.get(url, params=params)  # Выполняем GET-запрос к API
    if response.status_code != 200:
        # Если статус код не 200, выбрасываем исключение с подробностями ошибки
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    # Извлекаем новости из ответа, если они есть
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."  # Сообщение, если новости отсутствуют
    # Возвращаем заголовки первых 5 новостей, разделенных переносами строк
    return "\n".join([article["title"] for article in news_data[:5]])


def generate_post(topic):
    recent_news = get_recent_news(topic)

    # Генерация заголовка
    prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}"
    try:
        response_title = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=50,
            n=1,
            temperature=0.7,
        )
        title = response_title.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации заголовка: {str(e)}")

    # Генерация мета-описания
    prompt_meta = f"Напишите краткое, но информативное мета-описание для поста с заголовком: {title}"
    try:
        response_meta = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=100,
            n=1,
            temperature=0.7,
        )
        meta_description = response_meta.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации мета-описания: {str(e)}")

    # Генерация контента поста
    prompt_post = (
        f"Напишите подробный и увлекательный пост для блога на тему: {topic}, учитывая следующие последние новости:\n"
        f"{recent_news}\n\n"
        "Используйте короткие абзацы, подзаголовки, примеры и ключевые слова для лучшего восприятия и SEO-оптимизации."
    )
    try:
        response_post = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=1000,
            n=1,
            temperature=0.7,
        )
        post_content = response_post.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента поста: {str(e)}")

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }


@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    generated_post = generate_post(topic.topic)
    return generated_post


@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
