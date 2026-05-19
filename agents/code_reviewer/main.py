from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from reviewer import review_code, review_pr, CodeReview, PRReview

app = FastAPI(title="AI Code Reviewer")


class ReviewRequest(BaseModel):
    code: str
    language: str = "auto"


class PRReviewRequest(BaseModel):
    pr_url: str
    github_token: Optional[str] = None


@app.post("/review", response_model=CodeReview)
def review(payload: ReviewRequest):
    return review_code(payload.code, payload.language)


@app.post("/review/pr", response_model=PRReview)
def review_pull_request(payload: PRReviewRequest):
    try:
        return review_pr(payload.pr_url, payload.github_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {str(e)}")


@app.get("/")
def root():
    return {
        "message": "AI Code Reviewer",
        "endpoints": {
            "POST /review": "Review a code snippet — {code, language}",
            "POST /review/pr": "Review a GitHub PR — {pr_url, github_token?}",
        },
    }
