from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document
from dotenv import load_dotenv
import os

load_dotenv()

# Inicializa o cliente Qdrant apontando para o endereço do Docker local
client = QdrantClient(
    url=os.environ.get("QDRANT_URL"),
    api_key=os.environ.get("QDRANT_API_KEY"),
    cloud_inference=True
)

# Cria a coleção "movie" para armazenar os dados dos filmes e seus vetores
client.create_collection(
    collection_name="movie",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# Lista de filmes contendo título, descrição, ano de lançamento e gênero
menu_items = [
    ("A Origem", "Um ladrão especializado em roubo de segredos através dos sonhos recebe a missão de implantar uma ideia na mente de um alvo", "2010", "Ficção Científica"),
    ("Interestelar", "Uma equipe de astronautas viaja por um buraco de minhoca em busca de um novo lar para a humanidade", "2014", "Ficção Científica"),
    ("O Poderoso Chefão", "A história da família mafiosa Corleone e a ascensão de Michael como líder do império", "1972", "Crime"),
    ("Cidade de Deus", "A vida no subúrbio violento do Rio de Janeiro sob a perspectiva de jovens que crescem no crime", "2002", "Drama"),
    ("Titanic", "Um romance proibido entre classes sociais diferentes a bordo do navio que se torna palco de uma tragédia histórica", "1997", "Romance"),
    ("Vingadores: Ultimato", "Os heróis restantes se unem para desfazer os efeitos devastadores causados por Thanos", "2019", "Ação"),
    ("Matrix", "Um hacker descobre que a realidade é uma simulação e se junta à resistência contra as máquinas", "1999", "Ficção Científica"),
    ("O Senhor dos Anéis: A Sociedade do Anel", "Um jovem hobbit embarca em uma jornada para destruir um anel poderoso", "2001", "Fantasia"),
    ("Harry Potter e a Pedra Filosofal", "Um garoto descobre que é um bruxo e inicia sua jornada em uma escola de magia", "2001", "Fantasia"),
    ("Parasita", "Uma família pobre se infiltra na casa de uma família rica, desencadeando eventos inesperados", "2019", "Drama"),
    ("Coringa", "A origem sombria de um dos vilões mais icônicos de Gotham", "2019", "Drama"),
    ("Pantera Negra", "O rei de Wakanda precisa proteger seu povo e assumir seu papel como herói", "2018", "Ação"),
    ("Toy Story", "Brinquedos ganham vida quando humanos não estão por perto e vivem suas próprias aventuras", "1995", "Animação"),
    ("Procurando Nemo", "Um peixe-palhaço atravessa o oceano em busca de seu filho desaparecido", "2003", "Animação"),
    ("Homem-Aranha: Sem Volta Para Casa", "Peter Parker enfrenta consequências após ter sua identidade revelada", "2021", "Ação"),
    ("Duna", "Um jovem herdeiro luta pelo controle de um planeta desértico vital para o universo", "2021", "Ficção Científica"),
    ("Clube da Luta", "Um homem insatisfeito cria um clube secreto que se transforma em algo muito maior", "1999", "Drama"),
    ("Forrest Gump", "A vida extraordinária de um homem simples que testemunha momentos históricos", "1994", "Drama"),
    ("O Rei Leão", "Um jovem leão precisa assumir seu destino como rei após uma tragédia familiar", "1994", "Animação"),
    ("Gladiador", "Um general romano traído busca vingança enquanto luta como gladiador", "2000", "Ação"),
    ("A Lista de Schindler", "A história real de um empresário que salvou judeus durante o Holocausto", "1993", "Drama"),
    ("Jurassic Park", "Um parque com dinossauros clonados sai do controle e coloca todos em perigo", "1993", "Aventura"),
    ("Avatar", "Um ex-fuzileiro explora um planeta alienígena e se envolve em um conflito entre espécies", "2009", "Ficção Científica"),
    ("Coco", "Um garoto viaja ao mundo dos mortos para descobrir sua verdadeira identidade", "2017", "Animação"),
    ("Divertida Mente", "As emoções de uma garota ganham vida e tentam guiá-la em momentos difíceis", "2015", "Animação"),
    ("Os Incríveis", "Uma família de super-heróis precisa voltar à ação para salvar o mundo", "2004", "Animação"),
    ("Shrek", "Um ogro embarca em uma missão inesperada que muda sua vida para sempre", "2001", "Animação"),
    ("John Wick", "Um ex-assassino volta à ativa em busca de vingança", "2014", "Ação"),
    ("Mad Max: Estrada da Fúria", "Em um mundo pós-apocalíptico, sobreviventes lutam por liberdade", "2015", "Ação"),
    ("O Lobo de Wall Street", "A ascensão e queda de um corretor de ações envolvido em fraudes e excessos", "2013", "Biografia"),
    ("Bohemian Rhapsody", "A trajetória da banda Queen e de seu vocalista Freddie Mercury", "2018", "Biografia")
]

# Processa cada filme para criar uma estrutura de ponto (PointStruct) para o Qdrant
points = []
for i, menu_item in enumerate(menu_items):
    point = PointStruct(
        id=i,
        vector=Document(
            # Combina título e descrição para criar o embedding vetorial representativo do filme
            text=f"{menu_item[0]} {menu_item[1]}",
            model="sentence-transformers/all-MiniLM-L6-v2"
        ),
        payload={
            "item_name": menu_item[0],
            "description": menu_item[1],
            "year": menu_item[2],
            "category": menu_item[3],
        }
    )
    points.append(point)

# Envia todos os filmes processados (pontos) para a coleção no Qdrant
client.upsert(
  collection_name="movie",
  points=points,
)

# Define o texto da pergunta para a busca semântica
query_text = "animais marinhos em busca de aventura"

# Realiza a consulta para encontrar os filmes mais similares ao texto da pergunta
results = client.query_points(
    collection_name="movie",
    query=Document(text=query_text, model="sentence-transformers/all-MiniLM-L6-v2"),
    with_payload=True,
    limit=5
)

# Imprime os resultados da busca com seus respectivos scores de similaridade
for result in results.points:
    print(f"Item: {result.payload.get('item_name', 'N/A')}")
    print(f"Score: {result.score}")
    print(f"Description: {result.payload['description'][:150]}...")
    print(f"Year: {result.payload.get('year', 'N/A')}")
    print("---")