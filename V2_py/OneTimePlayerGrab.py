import requests

url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/players?scoringPeriodId=0&view=players_wl"
headers = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0',
    'x-fantasy-filter': '{"filterActive":null}',
    'x-fantasy-platform': 'kona-PROD-1dc40132dc2070ef47881dc95b633e62cebc9913',
    'x-fantasy-source': 'kona'
}
cookies = {
    'SWID': "{19CF9C33-584C-4AD9-B662-3E0445F92CD4}",
    'espn_s2': "AECdRzCYKvqgcz6UivaPk6%2Bieg43fAx5euJskD7kvJ7TiElN%2Fb%2F0ZyJP9kM2Syrh9S%2FL6ACNiG5EiExnJQY4jJXUvlREK7SBtScf%2B4wUTmT7M39%2FP1wrGWTffjpadaoTNyFYcAAAvPbjmkQi2yQWwILSnHxb82sBbDxmvYM%2F50JH3fpD3ih4cckdV%2BJOCZD3gvDSEovu0PuWu8pkn5Fz0y5ZI6dtsUHHoXSjUsjWVLTU0qP9GfHv6PM3G1eE%2FtfOuTEN3y0X7vI4JXPY%2FNC13Dpr%2BfiM7NmtkmA%2FUJcLpiUSdw%3D%3D"
}

response = requests.get(url, headers=headers, cookies=cookies)
player_data = response.json()