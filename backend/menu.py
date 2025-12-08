# menu.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, requests, json, re
import google.generativeai as genai

router = APIRouter()

# ✅ 위치 정보 모델
class Location(BaseModel):
    lat: float
    lon: float

# ✅ 키워드 모델
class KeywordRequest(BaseModel):
    keyword: str

# ✅ 맛집 검색 함수 (fallback 및 정제 포함)
def search_restaurants_by_menu(menu, lat, lon):
    print(f"[{menu}] 맛집 검색 중... lat={lat}, lon={lon}")

    headers = {
        "Authorization": f"KakaoAK {os.getenv('KAKAO_REST_API_KEY')}"
    }

    # 검색어 정제: "매콤한 제육볶음" → ["매콤한 제육볶음", "제육볶음"]
    keywords = [menu]
    if " " in menu:
        keywords.append(menu.split()[-1])

    for keyword in keywords:
        params = {
            "query": f"{keyword} 맛집",
            "x": lon,
            "y": lat,
            "radius": 3000,
            "size": 3
        }
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        res = requests.get(url, headers=headers, params=params)
        results = res.json()

        if results.get("documents"):
            return [
                {
                    "place_name": doc["place_name"],
                    "address": doc["road_address_name"] or doc["address_name"],
                    "distance": f"{doc['distance']}m"
                }
                for doc in results["documents"]
            ]

    return []

# ✅ 메뉴 추천 API
@router.post("/recommend-menu")
async def recommend_menu(loc: Location):
    try:
        prompt = f"""
        사용자의 GPS 위치는 위도 {loc.lat}, 경도 {loc.lon}입니다.

        이 위치를 기준으로 점심 식사 메뉴를 다음 조건에 따라 총 3가지 추천해 주세요:

        - 현실 식당에서 실제로 판매되는 구체적인 메뉴명을 사용해 주세요 (예: 김치찌개, 회덮밥, 제육볶음 등)
        - 두번 확인해서 실제 식당에 파는 메뉴인지 확인해주세요
        - 반복적인 메뉴는 피하고, 계절/위치/트렌드를 반영해 주세요 
        - 각 메뉴는 JSON 객체로 구성하고, 배열 형태로 3개를 출력해 주세요
        - 응답에는 설명 없이 JSON 결과만 출력해 주세요

        [
          {{
            "menu": "메뉴명",
            "description": "간단한 설명",
            "category": "한식/중식/일식/양식/기타"
          }}
        ]
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text

        match = re.search(r'\[.*\]', text, re.DOTALL)
        menus = json.loads(match.group()) if match else []

        for menu in menus:
            menu["restaurants"] = search_restaurants_by_menu(menu["menu"], loc.lat, loc.lon)

        return {"menus": menus}

    except Exception as e:
        print("🚨 에러 발생:", e)
        raise HTTPException(status_code=500, detail="Gemini 또는 맛집 추천 실패")

# ✅ 키워드 기반 위치 변환 API
@router.post("/convert-keyword")
async def convert_keyword(data: KeywordRequest):
    try:
        headers = {
            "Authorization": f"KakaoAK {os.getenv('KAKAO_REST_API_KEY')}"
        }
        params = {
            "query": data.keyword,
            "size": 1
        }

        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        res = requests.get(url, headers=headers, params=params)
        result = res.json()

        if result.get("documents"):
            doc = result["documents"][0]
            print(f"🔍 키워드 '{data.keyword}' → {doc['place_name']}, lat={doc['y']}, lon={doc['x']}")
            return {"lat": float(doc["y"]), "lon": float(doc["x"])}
        else:
            raise HTTPException(status_code=404, detail="해당 키워드로 장소를 찾을 수 없어요.")
    except Exception as e:
        print("🚨 키워드 변환 오류:", e)
        raise HTTPException(status_code=500, detail=str(e))