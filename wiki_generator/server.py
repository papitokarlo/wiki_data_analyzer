import uvicorn


if __name__ == "__main__":
    uvicorn.run("wiki_generator.main:app", reload=True)
