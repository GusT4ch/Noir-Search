"""
Sistema para buscar perguntas populares e tendências do Google
para usar nas pesquisas do Bing Rewards.
"""

import random
import requests
import json
from datetime import datetime
from pathlib import Path

# Lista de categorias populares para pesquisas
CATEGORIAS = [
    "tecnologia", "esportes", "noticias", "receitas", 
    "saude", "educacao", "entretenimento", "financas",
    "viagens", "moda", "games", "musica", "filmes"
]

# Prefixos para formar perguntas variadas
PREFIXOS = [
    "como", "qual", "o que e", "para que serve", "onde", 
    "quando", "por que", "quanto custa", "melhor", "pior",
    "significado de", "receita de", "dicas de"
]

# Palavras-chave populares por categoria
PALAVRAS_CHAVE = {
    "tecnologia": ["inteligencia artificial", "chatgpt", "python", "windows", "iphone", "android", "internet", "computador", "celular", "app"],
    "esportes": ["futebol", "basquete", "volei", "corrida", "academia", "treino", "exercicio", "caminhada", "yoga", "natacao"],
    "noticias": ["brasil", "mundo", "politica", "economia", "clima", "saude", "educacao", "seguranca", "transito", "meio ambiente"],
    "receitas": ["bolo", "pao", "lasanha", "strogonoff", "sopa", "salada", "suco", "pudim", "biscoito", "torta"],
    "saude": ["ansiedade", "estresse", "dieta", "exercicio", "sono", "meditacao", "vitaminas", "agua", "coracao", "cancer"],
    "educacao": ["enem", "vestibular", "curso", "faculdade", "ingles", "matematica", "portugues", "historia", "geografia", "redacao"],
    "entretenimento": ["netflix", "youtube", "spotify", "disney", "prime video", "hbo", "tiktok", "instagram", "whatsapp", "twitter"],
    "financas": ["investir", "poupanca", "acoes", "bitcoin", "dolar", "euro", "renda fixa", "aposentadoria", "imposto", "cartao de credito"],
    "viagens": ["praia", "montanha", "cidade", "hotel", "passagem", "mochilao", "turismo", "mochila", "mapa", "roteiro"],
    "moda": ["roupa", "calcado", "maquiagem", "cabelo", "unha", "perfume", "bolsa", "oculos", "relogio", "bijuteria"],
    "games": ["minecraft", "roblox", "fortnite", "fifa", "gta", "cod", "valorant", "lol", "freefire", "pubg"],
    "musica": ["pop", "rock", "sertanejo", "funk", "mpb", "eletronica", "rap", "pagode", "forro", "gospel"],
    "filmes": ["acao", "comedia", "drama", "terror", "suspense", "romance", "aventura", "ficcao", "animacao", "documentario"]
}

def buscar_tendencias_google():
    """
    Tenta buscar tendências do Google Trends (API pública limitada)
    Se falhar, usa lista local de termos populares.
    """
    try:
        # Tentativa de buscar tendências (funciona parcialmente)
        url = "https://trends.google.com/trends/api/dailytrends?hl=pt-BR&ed="
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Processa a resposta (formato JSONP)
            data = response.text.replace(")]}',", "")
            trends = json.loads(data)
            queries = []
            for trend in trends.get("default", {}).get("trendingSearches", []):
                queries.append(trend.get("title", {}).get("query", ""))
            return queries[:20]  # Retorna até 20 tendências
    except Exception as e:
        print(f"Não foi possível buscar tendências: {e}")
    
    # Fallback: gera perguntas baseadas em categorias populares
    return None

def gerar_perguntas_aleatorias(quantidade=40):
    """Gera uma lista de perguntas aleatórias baseadas em categorias."""
    perguntas = set()  # Usa set para evitar duplicatas
    
    # Adiciona perguntas baseadas em prefixos + palavras-chave
    while len(perguntas) < quantidade:
        categoria = random.choice(CATEGORIAS)
        palavra = random.choice(PALAVRAS_CHAVE[categoria])
        prefixo = random.choice(PREFIXOS)
        
        # Formata a pergunta de forma natural
        if prefixo in ["como", "qual", "quando", "onde", "por que", "quanto custa"]:
            pergunta = f"{prefixo} {palavra}"
        elif prefixo in ["o que e", "para que serve"]:
            pergunta = f"{prefixo} {palavra}?"
        elif prefixo in ["melhor", "pior"]:
            pergunta = f"{prefixo} {palavra} para"
        else:
            pergunta = f"{prefixo} {palavra}"
        
        # Limpa e adiciona
        pergunta = pergunta.strip().replace("  ", " ")
        perguntas.add(pergunta)
    
    # Converte para lista e garante exatamente a quantidade
    lista_perguntas = list(perguntas)[:quantidade]
    
    # Se não gerou o suficiente, completa com perguntas padrão
    while len(lista_perguntas) < quantidade:
        lista_perguntas.append(f"pesquisa sobre {random.choice(PALAVRAS_CHAVE['tecnologia'])}")
    
    return lista_perguntas

def salvar_queries(queries, arquivo="queries.txt"):
    """Salva a lista de queries no arquivo."""
    caminho = Path(arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("# Lista de pesquisas geradas automaticamente\n")
        f.write(f"# Data de geracao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("# " + "="*50 + "\n\n")
        for query in queries:
            f.write(f"{query}\n")
    print(f"{len(queries)} pesquisas salvas em {arquivo}")

if __name__ == "__main__":
    print("="*50)
    print("GERADOR DE PESQUISAS POPULARES")
    print("="*50)
    
    # Tenta buscar tendências do Google
    tendencias = buscar_tendencias_google()
    
    if tendencias:
        print(f"Encontradas {len(tendencias)} tendências do Google!")
        queries = tendencias
        # Se tiver menos de 40, completa com aleatórias
        if len(queries) < 40:
            aleatorias = gerar_perguntas_aleatorias(40 - len(queries))
            queries.extend(aleatorias)
    else:
        print("Não foi possível buscar tendências. Gerando perguntas aleatórias...")
        queries = gerar_perguntas_aleatorias(40)
    
    # Aleatoriza a ordem final
    random.shuffle(queries)
    
    # Mostra as primeiras 10 como exemplo
    print("\nExemplo das pesquisas geradas:")
    for i, q in enumerate(queries[:10], 1):
        print(f"  {i}. {q}")
    
    print(f"\n... e mais {len(queries)-10} pesquisas.")
    
    # Pergunta se quer salvar
    resposta = input("\nDeseja salvar estas 40 pesquisas no queries.txt? (s/n): ")
    if resposta.lower() == 's':
        salvar_queries(queries[:40])
        print("\nAgora execute: python noir_search.py")
    else:
        print("Nenhuma alteração foi salva.")
