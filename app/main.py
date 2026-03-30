from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import os
import re
import asyncio

import httpx
from bs4 import BeautifulSoup

app = FastAPI(title="Web Access API", version="1.0.0")

API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")


def check_auth(authorization: Optional[str]) -> None:
    if not API_KEY:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.replace("Bearer ", "").strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    focus: Optional[str] = "structure"


class XhsRequest(BaseModel):
    url: HttpUrl
    focus: Optional[str] = "selling_points"


async def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.text


def extract_text_from_html(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = og_title.get("content").strip()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    content = "\n".join(lines[:200])

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if src and src not in images:
            images.append(src)

    return {
        "title": title,
        "content": content,
        "images": images[:20],
    }


def build_analysis(content: str, focus: str) -> Dict[str, Any]:
    short = content[:1200]

    structure = "内容以开头引入、主体展开、结尾收束的常见网页表达结构为主。"
    if len(short) > 400:
        structure = "内容整体可拆为：引入背景/问题、主体信息展开、结尾总结或引导。"

    selling_points = [
        "内容中强调的核心信息点",
        "对用户价值或利益点的表达",
        "可能触发点击或转化的关键词"
    ]

    conversion_logic = "先用标题或关键信息吸引注意，再通过正文铺陈价值点，最后完成认知强化或行动引导。"

    if focus == "assets":
        structure = "建议按标题、关键句、配图、结论四部分整理素材。"
        conversion_logic = "适合提炼为PPT素材或内容拆解要点。"

    return {
        "structure": structure,
        "selling_points": selling_points,
        "conversion_logic": conversion_logic,
    }


@app.get("/health")
async def health():
    return {"ok": True, "name": "Web Access API", "version": "1.0.0"}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest, authorization: Optional[str] = Header(default=None)):
    check_auth(authorization)

    try:
        html = await fetch_html(str(req.url))
        extracted = extract_text_from_html(html)
        analysis = build_analysis(extracted["content"], req.focus or "structure")

        return JSONResponse({
            "title": extracted["title"],
            "content": extracted["content"],
            "images": extracted["images"],
            "analysis": analysis,
            "screenshot_url": None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {str(e)}")


@app.post("/xhs-note")
async def xhs_note(req: XhsRequest, authorization: Optional[str] = Header(default=None)):
    check_auth(authorization)

    try:
        html = await fetch_html(str(req.url))
        extracted = extract_text_from_html(html)

        title = extracted["title"]
        content = extracted["content"]

        author = ""
        m = re.search(r"作者[:：\s]+([^\n]+)", content)
        if m:
            author = m.group(1).strip()

        structure = "常见小红书结构：标题钩子 → 痛点/体验 → 产品或解决方案 → 结果强化。"
        selling_points = [
            "标题中的高吸引力关键词",
            "正文里的痛点与结果表达",
            "可被复用的种草卖点"
        ]
        conversion_logic = "通过情绪或痛点吸引点击，再用体验描述和结果感知推动用户建立兴趣与信任。"

        return JSONResponse({
            "title": title,
            "author": author,
            "content": content,
            "images": extracted["images"],
            "structure": structure,
            "selling_points": selling_points,
            "conversion_logic": conversion_logic,
            "screenshot_url": None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XHS note analyze failed: {str(e)}")
