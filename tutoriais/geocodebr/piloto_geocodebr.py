from pathlib import Path
import pandas as pd
from geocodebr import busca_por_cep

BASE = Path(__file__).resolve().parent
entrada = BASE / "amostra_ceps.csv"
saida_geojson = BASE / "saida_geocodebr.geojson"
saida_parquet = BASE / "saida_geocodebr.parquet"

# Lê CEP como texto para preservar zeros à esquerda.
df = pd.read_csv(entrada, dtype={"cep": "string"})
ceps = df["cep"].dropna().tolist()

# Teste inicial controlado: CEP -> coordenadas / GeoDataFrame.
gdf = busca_por_cep(
    cep=ceps,
    h3_res=9,
    resultado_gpd=True,
    verboso=True,
)

# Exporta formatos úteis para QGIS, Leaflet e análises futuras.
gdf.to_file(saida_geojson, driver="GeoJSON")
gdf.to_parquet(saida_parquet)

print("\nResumo do resultado:")
colunas = [c for c in ["cep", "estado", "municipio", "logradouro", "localidade", "lon", "lat"] if c in gdf.columns]
print(gdf[colunas].head(20).to_string(index=False))
print(f"\nGeoJSON: {saida_geojson}")
print(f"GeoParquet: {saida_parquet}")
