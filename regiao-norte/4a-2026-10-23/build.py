#!/usr/bin/env python3
"""Build the 4th Northern Region meeting from reviewed text and verified PDFs.
Formal PDF and integral HTML share all paragraphs, tables and selected figures.
No paid model calls; no changes to earlier publications.
"""
from __future__ import annotations
import argparse,csv,hashlib,html,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
import fitz,markdown2
from bs4 import BeautifulSoup,Comment
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY,TA_LEFT
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,PageBreak,NextPageTemplate,Image,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
ROOT=Path(__file__).resolve().parent
SITE='https://7it0.github.io/soe-salas-prototipo/regiao-norte/4a-2026-10-23/'
PDF='NT_Regiao_Norte_4a_23-10-2026.pdf'
NAME='José Aguiar de Lima Jr.'
ROLE='Especialista em Geoprocessamento'
UNIT='Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA'
TITLE='4ª Reunião de Avaliação das Condições Hidrometeorológicas da Região Norte'
EXPECTED={'inpe':'3963d47f224f9c3cfdff84cfec12381af32722235ee2af70c83727a0dd4f1c25','cemaden':'1ee23f7eeb60f903aa8cbb0fa2e53e226068d80c653d3244c2de3a065513e7b0','sgb':'4c4915b3056d58a947675e45925e819720ca9b1732965d353b6ffb47a8c3face','censipam':'b1c7b9a42df9393707a225cf0cb60e6e6279e7b6c0f5cbe90e938eb3a011f577','ons':'35a9dce60983d8bcdb9008e0ac57d061031c6c4a6272e9779fc9a4e02a40c8c7'}
LABELS={'inpe':'INPE/INMET','cemaden':'CEMADEN/MCTI','sgb':'SGB/CPRM','censipam':'CENSIPAM/SipamHidro','ons':'ONS'}
IDS=['resumo','escopo','inpe','cemaden','sgb','censipam','ons','cruzamentos','cenarios','regulacao','encerramento','qualidade','fontes']
FIGS={
'inpe':[(3,'Precipitação e anomalias — julho a setembro','Acumulado e desvio climatológico são informações diferentes; preservar a heterogeneidade espacial.'),(4,'Outubro parcial — até 22/10','A distribuição da chuva não demonstra recuperação homogênea dos rios.'),(8,'BAM — previsão de curto prazo','Janelas diárias de 24 a 27/10 em UTC. Chuva prevista não equivale a afluência.'),(9,'BAM — primeira e segunda semanas','Rodada de 21/10; janelas 21–27/10 e 28/10–03/11.'),(10,'BAM — terceira e quarta semanas','Janelas 04–10/11 e 11–17/11. O sinal varia no espaço e no tempo.'),(15,'Previsão conjunta — NDJ/2026–2027','Probabilidade de tercis. Áreas brancas não significam ausência de precipitação.')],
'cemaden':[(5,'Índice Integrado de Seca','Janelas de 3 e 6 meses. Preservar a diferença entre título e referência temporal dos mapas.'),(8,'Cotas e referência de longo termo','A coluna de desvios contém inconsistências aritméticas identificadas no capítulo 12; a figura original não foi corrigida.'),(9,'SPEI — chuva e demanda atmosférica','Setembro, janelas de 3, 6 e 12 meses. Não é medição direta da evapotranspiração real.'),(11,'TSI-12 — Negro, Tapajós, Amazonas e Madeira','Classes e valores transcritos da instituição, não recalculados pela NT.'),(12,'Roraima — seca e cota em Boa Vista','66 cm em 22/10; TSI -1,41. Percentual da cota não é percentual de vazão ou disponibilidade.'),(13,'TSI-12 — Xingu e Tocantins–Araguaia','Recortes orientais apresentam classes diferentes; preservar cada área contribuinte.'),(14,'TSI-12 — Solimões, Purus, Juruá e Tapajós','Índice normal pode coexistir com nível abaixo de uma referência em determinado dia.'),(25,'GloFAS — projeção subsazonal','Datas dos painéis cobrem cerca de cinco semanas apesar do título mencionar 45 dias.'),(30,'GloFAS — vazões naturais sazonais','Novembro/dezembro de 2026 e janeiro de 2027; ler categoria de anomalia e incerteza conjuntamente.')],
'sgb':[(4,'Síntese espacial da condição hidrológica','Branco–Negro, Madeira e Alto Solimões apresentam situações diferentes.'),(11,'Tabatinga — cenário por análogos','Modelo em testes operacionais; tendência recente não equivale ao saldo dos últimos 15 dias.'),(13,'Manaus — cenário por análogos','Trajetória condicionada ao modelo e à sua incerteza, não uma data garantida de recuperação.'),(16,'Caracaraí — cenário por análogos','A condição experimental indicada na apresentação é mantida.'),(19,'Porto Velho — cenário por análogos','Conferir a trajetória com observações e com as condições locais de navegação.'),(20,'Itaituba — cenário por análogos','A eventual recuperação não deve ser extrapolada a toda a rede hidrográfica.')],
'censipam':[(3,'Tabatinga — últimos 15 dias','Saldo negativo de 22 cm e reação nos últimos pontos são compatíveis.'),(7,'Boa Vista — anomalia negativa severa','Saldo de -22 cm em 15 dias; pequena reação final não elimina o déficit.'),(10,'Porto Velho — recuperação recente','Elevação de 196 cm no intervalo e normalidade na classificação apresentada.'),(18,'Comparação com a mesma data de 2023','Situação mais favorável que um ano extremo não demonstra ausência de risco futuro.'),(20,'Metodologia dos produtos de estiagem','Dt, variação em 30 dias, ICOE e IPO têm objetivos distintos dos índices bivariados de seca.'),(23,'Evolução do déficit nos últimos 30 dias','Recuperação e agravamento coexistem em diferentes recortes.'),(25,'Variação dos alertas ativos','Comparação entre 25/09 e 21/10; não equivale a inventário de danos comprovados.'),(30,'Manaus — prognóstico de cota mínima','Identificação Rio Negro nesta lâmina; preservar ressalva sobre a lâmina 8.')],
'ons':[(6,'Subsistema Norte — ENA e EAR','65% EAR até 22/10 não equivale ao volume útil de cada reservatório.'),(8,'Madeira — Santo Antônio','Setembro observado e cenário inferior para média de outubro são referências distintas.'),(9,'Jirau — condicionante de navegação','Replecionamento depende da inexistência de restrições no trecho informado pela fonte.'),(10,'Santo Antônio — operação observada','Nível de montante e vazões observadas até 22/10; não deduzir volume disponível apenas da cota.'),(12,'Xingu — Belo Monte/Pimental','700 m³/s do TVR em outubro e 100 m³/s do reservatório intermediário não são o mesmo controle.'),(14,'Araguari — Ferreira Gomes','Setembro em 54% da MLT; cenário inferior para outubro em 42% da MLT.'),(16,'Teles Pires — São Manoel','Setembro em 78% da MLT; cenário inferior para outubro em 69% da MLT.'),(18,'Uatumã — vazões naturais em Balbina','Médias naturais mensais não se confundem com as vazões do painel operativo.'),(19,'Balbina — operação e armazenamento','Ponto final: aproximadamente 55% VU, 248 m³/s afluentes e 728 m³/s defluentes.')]
}
CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:80px}body{margin:0;background:#f1f6f6;color:#243c48;font:17px/1.7 system-ui,sans-serif;overflow-wrap:anywhere}a{color:#07647a}header{padding:44px max(24px,calc((100vw - 1160px)/2));background:linear-gradient(115deg,#073c52,#116f6b);color:white}header h1{font-size:clamp(29px,4vw,47px);line-height:1.2;margin:16px 0}header p{max-width:1100px}.eyebrow{font-size:12px;letter-spacing:.1em;text-transform:uppercase}.credit{border-left:3px solid #9bd9ce;padding-left:17px;margin:22px 0;font-size:14px}.credit strong{font-size:17px}.notice{background:#fff5da;color:#4c421e;border-left:5px solid #c49b3d;padding:16px 20px;margin:24px 0}.actions{display:flex;gap:12px;flex-wrap:wrap}.actions a{border:1px solid #b9d4d8;border-radius:7px;background:white;color:#07556b;padding:11px 18px;text-decoration:none;font-weight:650;display:flex;align-items:center;justify-content:center;text-align:center}.actions a.primary{background:#c9f3e8;color:#064f4b;border-color:transparent}.actions a:focus-visible,button:focus-visible{outline:3px solid #efb63f;outline-offset:4px}nav{position:sticky;top:0;z-index:5;background:#fffffff5;border-bottom:1px solid #cbdde1;padding:13px 5%;display:flex;gap:22px;overflow-x:auto;white-space:nowrap}nav a{font-size:14px;font-weight:700;text-decoration:none}main{max-width:1210px;margin:28px auto;padding:0 24px}.chapter,.contents{background:white;border:1px solid #d8e4e7;border-radius:10px;padding:32px;margin:24px 0;min-width:0}h2{font-size:27px;line-height:1.3;color:#174e69}h3{font-size:20px;color:#146e60;margin-top:28px}.contents ul{columns:2;padding-left:20px}.contents li{margin:7px 0;break-inside:avoid}.tablewrap{max-width:100%;overflow:auto;margin:20px 0}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.55}th,td{border:1px solid #cadce1;padding:11px;vertical-align:top;text-align:left}th{background:#215575;color:white}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin:28px 0}.gallery figure:first-child{grid-column:1/-1}figure{margin:0;border:1px solid #cbdce2;border-radius:8px;overflow:hidden;min-width:0}figure img{display:block;width:100%;height:auto;cursor:zoom-in}figcaption{padding:16px;font-size:14px;line-height:1.55}figcaption strong{display:block;color:#15556d;margin-bottom:7px}.source{display:block;color:#607981;font-size:12px;margin:9px 0}.figlinks{display:flex;gap:18px;font-size:13px}.small{font-size:13px}.section-source{margin-top:20px;padding-top:14px;border-top:1px solid #d6e2e5;font-size:14px}footer{padding:30px max(24px,calc((100vw - 1160px)/2));background:#073c52;color:white;font-size:13px}footer a{color:white}dialog{border:0;border-radius:10px;width:min(96vw,1600px);max-height:96vh;padding:18px}dialog::backdrop{background:#001b2ae6}dialog img{width:100%;max-height:80vh;object-fit:contain}dialog button{display:block;margin:0 0 10px auto;padding:9px 16px;border:1px solid #bdd3dc;background:white;color:#07556b;border-radius:6px;font-weight:700;cursor:pointer}@media(max-width:800px){main{padding:0 12px}.chapter,.contents{padding:22px 18px}.contents ul{columns:1}.gallery{grid-template-columns:1fr}.actions a{width:100%}body{font-size:16px}}@media print{nav,.actions,dialog{display:none}header,footer{background:white;color:#16465c}body{background:white}.chapter{border:0;break-before:page}.gallery{display:block}figure{break-inside:avoid;margin:12px 0}}'''

def esc(x):return html.escape(str(x),quote=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalize(x):return re.sub(r'\s+',' ',x).strip()

def setup_fonts():
    choices=[Path('/usr/share/fonts/truetype/dejavu'),Path('/usr/share/fonts/truetype/liberation2')]
    for folder in choices:
        regular=folder/('DejaVuSans.ttf' if 'dejavu' in str(folder) else 'LiberationSans-Regular.ttf')
        bold=folder/('DejaVuSans-Bold.ttf' if 'dejavu' in str(folder) else 'LiberationSans-Bold.ttf')
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont('NT',str(regular)));pdfmetrics.registerFont(TTFont('NT-Bold',str(bold)))
            pdfmetrics.registerFontFamily('NT',normal='NT',bold='NT-Bold',italic='NT',boldItalic='NT-Bold');return 'NT','NT-Bold'
    return 'Helvetica','Helvetica-Bold'


def build(work:Path):
    work.mkdir(parents=True,exist_ok=True)
    for key,expected in EXPECTED.items():
        assert sha(work/'fontes'/f'{key}.pdf')==expected, 'Source identity mismatch: '+key
    md=(ROOT/'report.md').read_text(encoding='utf-8')
    soup=BeautifulSoup(markdown2.markdown(md,extras=['tables']),'html.parser')
    for i,h in enumerate(soup.find_all('h1')):h['id']=IDS[i]
    assert len(soup.find_all('h1'))==13
    assets=work/'assets';assets.mkdir(exist_ok=True)
    selected=[]
    for key,items in FIGS.items():
        source=fitz.open(work/'fontes'/f'{key}.pdf')
        for page,title,caption in items:
            number=len(selected)+1;src=f'assets/{key}_{page:02d}.png';p=source[page-1]
            p.get_pixmap(matrix=fitz.Matrix(1900/p.rect.width,1900/p.rect.width),alpha=False).save(work/src)
            selected.append({'number':number,'key':key,'page':page,'title':title,'caption':caption,'src':src})
        source.close()
    assert len(selected)==38
    # HTML: every reviewed paragraph and table; figures appear within their vertical.
    body=[];chapter=False
    for el in soup.contents:
        if isinstance(el,Comment):
            if 'figures:' in str(el):
                key=str(el).split('figures:')[1].strip();gallery=[]
                for item in [f for f in selected if f['key']==key]:
                    s=item['src'];n=item['number'];p=item['page']
                    gallery.append(f'<figure id="fig-{n:02d}"><a href="{s}" data-zoom="{s}"><img src="{s}" alt="{esc(item["title"])} — {LABELS[key]}, p. {p}" loading="eager"></a><figcaption><strong>Figura {n:02d} · {esc(item["title"])}</strong>{esc(item["caption"])}<span class="source">Reprodução da apresentação {LABELS[key]}, página {p} do PDF recebido.</span><span class="figlinks"><a href="{s}" data-zoom="{s}">Ampliar figura</a><a href="fontes/{key}.pdf#page={p}" target="_blank" rel="noopener">Consultar fonte</a></span></figcaption></figure>')
                body.append('<div class="gallery">'+''.join(gallery)+'</div>')
            continue
        if getattr(el,'name',None)=='h1':
            if chapter:body.append('</section>')
            chapter=True;body.append(f'<section class="chapter" id="{el["id"]}"><h2>{esc(el.get_text())}</h2>')
        elif getattr(el,'name',None)=='h2':body.append('<h3>'+esc(el.get_text())+'</h3>')
        elif getattr(el,'name',None)=='table':body.append('<div class="tablewrap">'+str(el)+'</div>')
        else:body.append(str(el))
    body.append('<div class="section-source"><strong>Apresentações integrais:</strong> '+ ' · '.join(f'<a href="fontes/{k}.pdf">{v}</a>' for k,v in LABELS.items())+'</div></section>')
    toc=''.join(f'<li><a href="#{h["id"]}">{esc(h.get_text())}</a></li>' for h in soup.find_all('h1'))
    credit=f'<div class="credit">Supervisionado por <strong>{NAME}</strong><br>{ROLE}<br>{UNIT}<br>Elaboração com suporte de inteligência artificial (IA).</div>'
    nav=''.join(f'<a href="#{k}">{label}</a>' for k,label in [('resumo','Síntese'),('inpe','INPE/INMET'),('cemaden','CEMADEN'),('sgb','SGB'),('censipam','CENSIPAM'),('ons','ONS'),('cruzamentos','Cruzamentos'),('encerramento','Encerramento'),('fontes','Fontes')])
    page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="author" content="Supervisão: {NAME} — {ROLE} — SOE/ANA; suporte de IA"><title>Região Norte · 4ª reunião · NT integral</title><style>{CSS}</style></head><body id="topo"><header><div class="eyebrow">SOE/ANA — Gabinete | Nota Técnica</div><h1>{TITLE}</h1><p>23 de outubro de 2026 · Consolidação após o encerramento · Edição 1.0</p><p>Cinco verticais · 38 reproduções das apresentações · Conteúdo integral</p>{credit}<div class="notice"><strong>Próxima reunião: 4 de dezembro de 2026 — Sala de Crise.</strong><br>Mudança de denominação em razão do El Niño, informada no encerramento.</div><div class="actions"><a href="#resumo">Ler Nota Técnica — versão navegável</a><a class="primary" href="documentos/{PDF}" download>Nota Técnica integral — PDF</a><a href="indicadores.csv" download>Dados e indicadores — CSV</a></div></header><nav>{nav}</nav><main><section class="contents"><h2>Sumário</h2><ul>{toc}</ul><p class="small">O PDF contém o mesmo texto e as mesmas figuras, com sumário paginado e anexos em paisagem. Os encaminhamentos informados são separados das recomendações analíticas.</p></section>{''.join(body)}</main><footer>{credit}<p>Reunião de 23/10/2026 · Repositório pessoal de protótipos. A consolidação não substitui ata, ato administrativo ou manifestação institucional formal.</p><a href="#topo">Voltar ao início</a></footer><dialog id="zoom"><button type="button">Fechar ×</button><img alt="Reprodução ampliada"><p id="zoom-text"></p></dialog><script>const d=document.querySelector('#zoom');document.querySelectorAll('[data-zoom]').forEach(a=>a.addEventListener('click',e=>{{if(!d.showModal)return;e.preventDefault();const f=a.closest('figure');d.querySelector('img').src=a.dataset.zoom;d.querySelector('img').alt=f.querySelector('img').alt;document.querySelector('#zoom-text').textContent=f.querySelector('figcaption').innerText;d.showModal();}}));d.querySelector('button').onclick=()=>d.close();d.addEventListener('click',e=>{{if(e.target===d)d.close();}});</script></body></html>'''
    (work/'index.html').write_text(page,encoding='utf-8')
    parsed=BeautifulSoup(page,'html.parser')
    for p in soup.find_all('p'):assert normalize(p.get_text()) in normalize(parsed.get_text())
    assert len(parsed.select('figure img'))==38
    # CSV: documented values, not invented series.
    rows=[]
    def row(inst,local,indicator,value,unit,period,kind,p):rows.append([inst,local,indicator,value,unit,period,kind,p])
    tsi=[('Boa Vista / Branco','-1,41',12),('Manaus / Negro','-1,35',11),('Santarém / Tapajós','-0,61',11),('Óbidos / Amazonas','-0,34',11),('Santo Antônio / Madeira','0,15',11),('Belo Monte / Xingu','-1,18',13),('Tucuruí','-1,45',13),('Araguatins','-1,41',13),('Descarreto','-1,31',13),('Conceição do Araguaia','-1,50',13),('Manacapuru','-0,23',14),('Tabatinga','-0,25',14),('Beruri / Purus na fonte','0,22',14),('Santos Dumont / Juruá','-0,20',14)]
    for local,val,p in tsi:row('CEMADEN',local,'TSI-12',val,'adimensional','Outubro/2026 parcial','índice',p)
    levels=[('Tabatinga',-22,3),('Rio Branco/AC',210,4),('Beruri',-128,5),('Cucuí',44,6),('Boa Vista',-22,7),('Manaus',-102,8),('Guajará-Mirim',-10,9),('Porto Velho',196,10),('Óbidos',-79,11),('Itaituba',-29,12),('Santarém',-54,13),('Pedra do Ó',-7,14),('Xambioá',9,15),('Marabá',-30,16)]
    for local,val,p in levels:row('CENSIPAM',local,'Variação de cota em 15 dias',val,'cm','Janela apresentada em 23/10/2026','observado',p)
    flow=[('Santo Antônio',6387,121,5917,91,8),('Pimental',807,76,696,64,12),('Ferreira Gomes',247,54,115,42,14),('São Manoel',540,78,604,69,16),('Balbina',165,53,211,77,18)]
    for local,obs,pct,forecast,fp,p in flow:
        row('ONS',local,'Vazão natural média',obs,'m³/s','Setembro/2026','observado mensal',p);row('ONS',local,'Vazão natural relativa à MLT',pct,'% MLT','Setembro/2026','observado mensal',p)
        row('ONS',local,'Vazão natural média — cenário inferior',forecast,'m³/s','Outubro/2026','cenário condicional',p);row('ONS',local,'Cenário inferior relativo à MLT',fp,'% MLT','Outubro/2026','cenário condicional',p)
    for indicator,value,unit in [('Volume útil',55,'% VU'),('Vazão afluente',248,'m³/s'),('Vazão defluente',728,'m³/s')]:row('ONS','Balbina',indicator,value,unit,'Painel até 22/10/2026','posição destacada',19)
    row('ONS','Subsistema Norte','Energia armazenada',65,'% EARmáx','22/10/2026','observado',6)
    row('CEMADEN','Boa Vista','Cota diária',66,'cm','22/10/2026','observado; zero da régua local',12)
    with (work/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';');writer.writerow(['instituicao','local','indicador','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf'])
        for r in rows:
            key={'CEMADEN':'cemaden','CENSIPAM':'censipam','ONS':'ons'}[r[0]];writer.writerow(r+[SITE+f'fontes/{key}.pdf#page={r[7]}'])
    # Formal document styles, headings and running identification.
    normal,bold=setup_fonts();blue=colors.HexColor('#215575');green=colors.HexColor('#1b6d60')
    styles={
      'body':ParagraphStyle('Body',fontName=normal,fontSize=10.2,leading=14.5,alignment=TA_JUSTIFY,spaceAfter=8),
      'h1':ParagraphStyle('Heading1',fontName=bold,fontSize=15.5,leading=20,textColor=blue,spaceAfter=13,keepWithNext=True),
      'h2':ParagraphStyle('Heading2',fontName=bold,fontSize=11.3,leading=15,textColor=green,spaceBefore=12,spaceAfter=7,keepWithNext=True),
      'cell':ParagraphStyle('Cell',fontName=normal,fontSize=8.3,leading=11,spaceAfter=0),
      'head':ParagraphStyle('TableHead',fontName=bold,fontSize=8.3,leading=11,textColor=colors.white),
      'cover':ParagraphStyle('Cover',fontName=bold,fontSize=20,leading=26,textColor=blue,alignment=TA_CENTER,spaceAfter=16),
      'center':ParagraphStyle('Center',fontName=normal,fontSize=11,leading=16,alignment=TA_CENTER,spaceAfter=10),
      'caption':ParagraphStyle('Caption',fontName=normal,fontSize=9,leading=12,spaceAfter=7),
      'annex':ParagraphStyle('Annex',fontName=bold,fontSize=13.5,leading=17,textColor=blue,spaceAfter=9,keepWithNext=True)
    }
    def inline(node):
        s=node.decode_contents().replace('<strong>','<b>').replace('</strong>','</b>').replace('<em>','<i>').replace('</em>','</i>')
        return s.replace('−','-')
    def par(text,style='body'):return Paragraph(text,styles[style])
    def header_footer(c,doc):
        w,h=c._pagesize;c.saveState();c.setFont(normal,7.5);c.setFillColor(colors.HexColor('#62747d'))
        c.drawString(2*cm,h-1.15*cm,'SOE/ANA — GABINETE  |  Região Norte — 4ª reunião — 23/10/2026')
        c.setStrokeColor(colors.HexColor('#bdcfd7'));c.line(2*cm,h-1.35*cm,w-2*cm,h-1.35*cm)
        c.line(2*cm,1.9*cm,w-2*cm,1.9*cm);c.setFont(normal,7)
        c.drawCentredString(w/2,1.52*cm,f'Supervisionado por {NAME} · {ROLE}')
        c.drawCentredString(w/2,1.17*cm,'Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)')
        c.restoreState()
    class NTDoc(BaseDocTemplate):
        def afterFlowable(self,f):
            if hasattr(f,'toc_key'):
                self.canv.bookmarkPage(f.toc_key);self.canv.addOutlineEntry(f.getPlainText(),f.toc_key,0,False)
                self.notify('TOCEntry',(0,f.getPlainText(),self.page,f.toc_key))
    out=work/'documentos';out.mkdir(exist_ok=True);pdfpath=out/PDF
    portrait_frame=Frame(2*cm,2.4*cm,A4[0]-4*cm,A4[1]-4.2*cm,id='p',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    ls=landscape(A4);land_frame=Frame(1.7*cm,2.4*cm,ls[0]-3.4*cm,ls[1]-4.2*cm,id='l',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc=NTDoc(str(pdfpath),pagesize=A4,title='Nota Técnica — Região Norte — 23/10/2026',author=f'{NAME} — {ROLE} — SOE/ANA; suporte de IA')
    doc.addPageTemplates([PageTemplate(id='portrait',frames=[portrait_frame],onPage=header_footer,pagesize=A4),PageTemplate(id='landscape',frames=[land_frame],onPage=header_footer,pagesize=ls)])
    story=[Spacer(1,0.55*cm),par('NOTA TÉCNICA<br/>REGISTRO ANALÍTICO','cover'),par(esc(TITLE),'center'),par('23 de outubro de 2026','center'),par('Avaliação integrada das apresentações do<br/><b>INPE/INMET, CEMADEN, SGB, CENSIPAM e ONS</b>','center'),Spacer(1,.3*cm),par(f'<b>Supervisionado por {NAME}</b><br/>{ROLE}<br/>{UNIT}<br/>Elaboração com suporte de inteligência artificial (IA).','center')]
    cover_rows=[('Objeto','Consolidação técnica após o encerramento da reunião.'),('Base documental','Cinco PDFs recebidos; mapas, tabelas e gráficos originais.'),('Versão','1.0 — 23/10/2026. Não substitui ata ou ato administrativo.'),('Próxima reunião','04/12/2026 — Sala de Crise, em razão do El Niño, conforme informado no encerramento.')]
    t=Table([[par(esc(a),'head'),par(esc(b),'cell')] for a,b in cover_rows],colWidths=[3.3*cm,13.7*cm]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),blue),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#aabfc8')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story+=[Spacer(1,.45*cm),t,Spacer(1,.55*cm),par('Tese técnica consolidada','h2'),par('A seca e a resposta dos rios são heterogêneas. Branco–Negro concentra preocupação, enquanto o Madeira apresenta condição relativa mais favorável. A transição climática exige vigilância por bacia, distinguindo disponibilidade natural, armazenamento, navegação e restrições operativas.'),PageBreak(),par('SUMÁRIO','h1')]
    tocobj=TableOfContents();tocobj.dotsMinLevel=0;tocobj.levelStyles=[ParagraphStyle('TOC',fontName=normal,fontSize=9.5,leading=13.5,spaceBefore=5,leftIndent=0,firstLineIndent=0)];story+=[tocobj,PageBreak()]
    first=True
    for el in soup.contents:
        name=getattr(el,'name',None)
        if name=='h1':
            if not first:story.append(PageBreak())
            first=False;h=par(esc(el.get_text()),'h1');h.toc_key=el['id'];story.append(h)
        elif name=='h2':story.append(par(esc(el.get_text()),'h2'))
        elif name=='p':story.append(par(inline(el)))
        elif name=='table':
            trs=el.find_all('tr');n=len(trs[0].find_all(['th','td']));data=[]
            for i,tr in enumerate(trs):data.append([par(inline(td),'head' if i==0 else 'cell') for td in tr.find_all(['th','td'])])
            ratios={2:[.30,.70],3:[.25,.34,.41],4:[.29,.24,.20,.27]}.get(n,[1/n]*n)
            tb=Table(data,colWidths=[(A4[0]-4*cm)*v for v in ratios],repeatRows=1,hAlign='LEFT')
            tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),blue),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f5f7')]),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#bbcdd4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]));story+=[Spacer(1,5),tb,Spacer(1,10)]
    story+=[par('Arquivos integrais e rastreabilidade','h2')]
    for key,label in LABELS.items():story.append(par(f'{esc(label)}: <link href="{SITE}fontes/{key}.pdf" color="#215575">consultar apresentação integral</link>.','caption'))
    story+=[NextPageTemplate('landscape'),PageBreak()]
    for ki,(key,label) in enumerate(LABELS.items()):
        group=[f for f in selected if f['key']==key]
        for j,item in enumerate(group):
            if ki or j:story.append(PageBreak())
            if j==0:
                h=par(f'ANEXO {chr(65+ki)} — {esc(label)}','annex');h.toc_key='anexo-'+key;story.append(h)
            else:story.append(par(f'Anexo {chr(65+ki)} — {esc(label)}','caption'))
            story.append(par(f'Figura {item["number"]:02d}. {esc(item["title"])}','annex'))
            iw,ih=PILImage.open(work/item['src']).size;maxw=ls[0]-3.8*cm;maxh=ls[1]-7.6*cm;scale=min(maxw/iw,maxh/ih)
            im=Image(str(work/item['src']),width=iw*scale,height=ih*scale);im.hAlign='CENTER';story.append(im);story.append(Spacer(1,7))
            story.append(par(esc(item['caption']),'caption'))
            story.append(par(f'Reprodução de {esc(label)}, página {item["page"]} do PDF recebido. <link href="{SITE}fontes/{key}.pdf#page={item["page"]}" color="#215575">Fonte integral</link>.','caption'))
    doc.multiBuild(story)
    # Add total-page numbering after TOC pagination has converged; no layout shifts.
    generated=fitz.open(pdfpath);total=len(generated)
    for i,p in enumerate(generated):p.insert_text((p.rect.width-112,p.rect.height-17),f'Página {i+1} de {total}',fontname='helv',fontsize=8,color=(.25,.35,.40))
    final=pdfpath.with_suffix('.checked.pdf');generated.save(final,garbage=4,deflate=True);generated.close();final.replace(pdfpath)
    checked=fitz.open(pdfpath);text=normalize(' '.join(p.get_text() for p in checked))
    for node in soup.find_all('p'):
        expected=normalize(node.get_text()).replace('−','-')
        assert expected in text, 'PDF missing paragraph: '+expected[:80]
    for node in soup.select('th,td'):
        assert normalize(node.get_text()).replace('−','-') in text, 'PDF table cell missing'
    for i,p in enumerate(checked):assert NAME in p.get_text() and 'inteligência artificial' in p.get_text(),f'Credit missing {i+1}'
    assert 'SUMÁRIO' in checked[1].get_text() and len(checked.get_toc())==18
    assert len([p for p in checked if p.rect.width>p.rect.height])==38
    assert sum(len(p.get_images()) for p in checked)>=38
    qa=work/'qa';qa.mkdir(exist_ok=True)
    for i,p in enumerate(checked):p.get_pixmap(matrix=fitz.Matrix(.85,.85),alpha=False).save(qa/f'pagina-{i+1:02d}.png')
    manifest={'meeting':'4ª Região Norte','date':'2026-10-23','edition':'1.0','generated_at_utc':datetime.now(timezone.utc).isoformat(),'sources':{k:{'sha256':sha(work/'fontes'/f'{k}.pdf'),'pages':len(fitz.open(work/'fontes'/f'{k}.pdf'))} for k in LABELS},'figures':selected,'figure_count':38,'pdf_pages':total,'indicator_rows':len(rows),'pdf_sha256':sha(pdfpath),'report_sha256':sha(ROOT/'report.md'),'next_meeting':{'date':'2026-12-04','designation':'Sala de Crise','reason':'El Niño','provenance':'Informação do responsável após o encerramento'},'checks':{'all_paragraphs_in_pdf':True,'all_table_cells_in_pdf':True,'same_figures_html_pdf':True,'toc_entries':18,'credits_every_page':True}}
    (work/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copyfile(ROOT/'report.md',work/'report.md');shutil.copyfile(__file__,work/'builder_reference.py')
    print('VALIDATED',total,'pages; 38 figures; ',len(rows),'indicators; all text/table cells preserved; next meeting 04/12.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();build(args.output.resolve())
