#!/usr/bin/env python3
"""Build the live-meeting preview from its existing HTML and verified PDFs.
No external source search, no change to earlier meetings, no invented decisions.
"""
from pathlib import Path
import argparse,csv,hashlib,html,json,re,shutil
from datetime import datetime,timezone
import fitz
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,SimpleDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,PageBreak,NextPageTemplate,Image
from reportlab.platypus.tableofcontents import TableOfContents
ROOT=Path(__file__).resolve().parent
SITE='https://7it0.github.io/soe-salas-prototipo/regiao-sul/9a-2026-10-27/'
PDF='NT_Regiao_Sul_9a_27-10-2026_PREVIA.pdf'
ANNEX='Anexo_I_Regiao_Sul_27-10-2026_PREVIA.pdf'
NAME='José Aguiar de Lima Jr.'
ROLE='Especialista em Geoprocessamento'
LABELS={'inmet':'INMET','cemaden':'CEMADEN','ons':'ONS','sgb':'SGB'}
HASHES={'inmet':'fd3b72f8b9af827ac2647a99f5790787e20479a69c85225931e77df23bc4d420','cemaden':'e137a004d52fa5e24a3fa68834226049326b26a0dfb563e779cad99aa7383844','ons':'6788619e815bf9a0ca47e571fcb610c756a848310100afb93e7704b98a6a3aa9','sgb':'e8e353e309cf68b209d42d776e29b1b7c9147c472f10e383f117225c629ae4a5'}
FIGS={
'inmet':[(4,'Anomalias de precipitação — 30 e 90 dias','As janelas mostram antecedentes diferentes e não devem ser somadas.'),(5,'Precipitação nas estações — outubro parcial','Acumulados pontuais; a tabela não explicita horário de corte.'),(7,'Precipitação prevista — 27/10 a 02/11','COSMO, GFS e GFS Ensemble; distribuição espacial não uniforme.'),(8,'GFS Ensemble — quinze dias','Rodadas de 26 e 27/10, até 11/11; horizontes sobrepostos.'),(17,'Probabilidades de intensidade do ENSO','Produto NOAA reproduzido pelo INMET; contexto climático, não previsão de cheia local.'),(24,'Prognóstico climático NDJ','Preservar distinção entre anomalias previstas de chuva e temperatura.'),(27,'Comparação dos produtos sazonais','Convergência regional não determina o dia e a magnitude de um evento.')],
'cemaden':[(2,'Chuva nos últimos 30 dias','Janela de 26/09 a 26/10; acumulado e anomalia são variáveis distintas.'),(3,'TSI-12 e vazão de Itaipu','Déficit de longo período pode coexistir com aporte mensal acima da média.'),(4,'TSI-6 — Paranapanema e Iguaçu','Classes escritas na fonte são preservadas; anotação histórica de Jurumirim requer conferência.'),(5,'TSI-6 — Uruguai, Jacuí e Ijuí','Condição normal no índice de seca não exclui inundação em uma estação.'),(8,'GEFS — Itaipu e Iguaçu','Acumulados de 14 dias: cerca de 109 e 113 mm, respectivamente.'),(9,'GEFS — Uruguai e Jacuí','Cerca de 65 e 39 mm; curvas previstas abaixo da climatologia desenhada.'),(10,'Tendências da terceira e quarta semanas','Janelas 09–16 e 16–23/11; CFS/NOAA e ECMWF.'),(11,'GloFAS subsazonal','Ler anomalia e incerteza conjuntamente; a data 31/11 é uma inconsistência da fonte.'),(16,'GloFAS sazonal NDJ','Novembro/dezembro de 2026 e janeiro de 2027, pelo contexto da edição.')],
'ons':[(5,'ENA por bacia','Outubro parcial até 25/10; percentuais da MLT não são vazões.'),(6,'Armazenamento dos principais reservatórios','Percentuais VU por aproveitamento; não medem sozinhos amortecimento de cheias.'),(9,'Iguaçu — características e restrições','Máximos apresentados para Salto Santiago; verificar a aplicação operativa.'),(10,'Iguaçu — operação observada','Há divergência entre 82% no diagrama e 79% no gráfico de Salto Santiago.'),(11,'Baixo Iguaçu — cenários de vazão','Trajetória central em recessão, com dispersão entre cenários.'),(13,'Uruguai — Barra Grande e Machadinho','Painéis até 25/10; não equivalem aos níveis locais do SGB em 27/10.'),(15,'Foz do Chapecó — cenários','Percentis superiores mostram possibilidade de novos pulsos, não certeza.'),(16,'Jacuí e Taquari–Antas — condicionantes','Passo Real 2.400 m³/s; Dona Francisca 1.450 m³/s sazonal, conforme a fonte.'),(17,'Passo Real — operação e armazenamento','64% VU, 428 m³/s afluentes e 266 m³/s defluentes; 80% não é o estoque corrente.'),(18,'Dona Francisca — cenários','A mediana e os extremos do conjunto não constituem regras de defluência.')],
'sgb':[(3,'Situação dos sistemas de alerta em 27/10','Caí, Taquari, Guaíba e Uruguai; condições espacialmente distintas.'),(4,'Níveis e percentis históricos','Referência para o mesmo dia; percentil não é cota local de inundação.'),(7,'Guaíba — nível e limiares','Preservar a referência da estação e não extrapolar para outra régua.'),(8,'Uruguai — inundação em curso','Condição explicitamente indicada na apresentação.'),(9,'Uruguai — previsão de curto prazo','Emissão de 27/10 às 07h; trajetórias diferentes entre estações.'),(10,'Uruguai — propagação para os trechos seguintes','Acompanhar limiares e incertezas; não inferir encerramento pelo recuo a montante.')]
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(t):return html.escape(str(t),quote=True)
def norm(t):return re.sub(r'\s+',' ',t).strip().replace('−','-')

def build(out,source_dir):
 out.mkdir(parents=True,exist_ok=True)
 for name in ['fontes','assets','documentos','qa']:(out/name).mkdir(exist_ok=True)
 for key,digest in HASHES.items():
  source=source_dir/(key+'.pdf');assert sha(source)==digest,'Source differs from uploaded PDF: '+key
  shutil.copyfile(source,out/'fontes'/(key+'.pdf'))
 s=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
 assert not s.select('figure'),'Preview builder requires original text edition'
 original_sections={x['id']:str(x) for x in s.select('main section')}
 paras=[norm(p.get_text(' ',strip=True)) for p in s.select('main section p')]
 cells=[norm(p.get_text(' ',strip=True)) for p in s.select('main th, main td')]
 s.select_one('.notice').clear();s.select_one('.notice').append('PRÉVIA TÉCNICA 0.2 — quatro verticais, cruzamentos, Anexo I e reproduções dos PDFs enviados. Edição de acompanhamento, ainda sem registro de encerramento ou deliberações finais.')
 s.select_one('footer > p').string='27/10/2026 · Prévia 0.2 · Consolidação documental em acompanhamento; encerramento e deliberações ainda não informados.'
 s.select_one('.actions').clear()
 actions=BeautifulSoup(f'<a href="#executivo">Ler NT — versão navegável</a><a class="primary" href="documentos/{PDF}" download>Nota Técnica integral · PDF preliminar</a><div class="data-actions"><a href="indicadores.csv" download>Dados e indicadores · CSV</a><a href="#anexo-i">Anexo I — Reunião em números</a></div>','html.parser')
 for el in list(actions.contents):s.select_one('.actions').append(el)
 selected=[]
 for key,items in FIGS.items():
  src=fitz.open(source_dir/(key+'.pdf'));gallery=s.new_tag('div',attrs={'class':'gallery'})
  for page,title,caption in items:
   n=len(selected)+1;path=f'assets/{key}_{page:02}.png';p=src[page-1]
   p.get_pixmap(matrix=fitz.Matrix(1700/p.rect.width,1700/p.rect.width),alpha=False).save(out/path)
   item={'number':n,'institution':LABELS[key],'key':key,'page':page,'title':title,'caption':caption,'src':path};selected.append(item)
   fragment=BeautifulSoup(f'<figure id="fig-{n:02}"><a href="{path}" data-zoom="{path}"><img src="{path}" alt="{esc(title)}" loading="lazy"></a><figcaption><strong>Figura {n:02} — {esc(title)}</strong>{esc(caption)}<span class="source">Fonte: {LABELS[key]}, p. {page} do PDF recebido. Reprodução original.</span><a href="fontes/{key}.pdf#page={page}" target="_blank" rel="noopener">Consultar apresentação</a></figcaption></figure>','html.parser').figure;gallery.append(fragment)
  s.find(id=key).append(gallery);src.close()
 assert len(selected)==32
 s.find(id='anexo-i').append(BeautifulSoup(f'<p class="annex-access"><a href="documentos/{ANNEX}" download>Anexo I — PDF para consulta e encaminhamento</a></p>','html.parser').p)
 links=s.new_tag('p',attrs={'class':'source-access'})
 for key,label in LABELS.items():
  a=s.new_tag('a',href=f'fontes/{key}.pdf',target='_blank',rel='noopener');a.string=label+' — PDF integral';links.append(a);links.append(' · ')
 s.find(id='fontes').append(links)
 dialog=BeautifulSoup('<dialog id="zoom"><button type="button">Fechar ×</button><img alt="Reprodução ampliada"></dialog>','html.parser').dialog;s.body.append(dialog)
 js=s.new_tag('script');js.string="const d=document.querySelector('#zoom');document.querySelectorAll('[data-zoom]').forEach(a=>a.onclick=e=>{if(!d.showModal)return;e.preventDefault();d.querySelector('img').src=a.dataset.zoom;d.showModal();});d.querySelector('button').onclick=()=>d.close();d.onclick=e=>{if(e.target===d)d.close();};";s.body.append(js)
 (out/'index.html').write_text(str(s),encoding='utf-8')
 # Long-format numerical companion, separate from the reader-facing annex.
 rows=[]
 def add(inst,local,indicator,value,unit,period,nature,page):rows.append([inst,local,indicator,value,unit,period,nature,page])
 for local,value in [('Dionísio Cerqueira',571.6),('Laranjeiras do Sul',571.4)]:add('INMET',local,'Precipitação',value,'mm','Outubro parcial; corte não explicitado','observado_parcial',5)
 for local,value,pg,scale,cls in [('Porto Primavera',-1.04,3,12,'seca moderada'),('Itaipu',-.51,3,12,'seca fraca'),('Rosana',1.44,4,6,'normal na fonte'),('Capivara',1.48,4,6,'normal na fonte'),('Jurumirim',.57,4,6,'normal na fonte'),('Salto Santiago',1.43,4,6,'normal na fonte'),('Segredo',1.48,4,6,'normal na fonte'),('Salto Caxias',1.39,4,6,'normal na fonte'),('Foz do Chapecó',.72,5,6,'normal na fonte'),('Barra Grande',.97,5,6,'normal na fonte'),('Passo Real',.22,5,6,'normal na fonte'),('São José',-.36,5,6,'normal na fonte')]:add('CEMADEN',local,'TSI-'+str(scale),value,'adimensional','Outubro parcial','índice; '+cls,pg)
 add('CEMADEN','Itaipu','Vazão natural relativa à MLT',185,'% MLT','Outubro parcial','observado_parcial',3)
 for local,value,pg in [('Paranapanema',108,7),('Itaipu',109,8),('Iguaçu',113,8),('Uruguai',65,9),('Jacuí',39,9)]:add('CEMADEN',local,'Precipitação GEFS em 14 dias',value,'mm','Rodada 27/10/2026 00 UTC','previsão; aproximado',pg)
 for local,value in [('Iguaçu',289),('Uruguai',174),('Jacuí',165),('Capivari',218)]:add('ONS',local,'ENA',value,'% MLT','Outubro parcial até 25/10','observado_parcial',5)
 for local,value in [('GBM / Foz do Areia',87),('Salto Santiago',82),('Barra Grande',92),('Passo Fundo',72),('Machadinho',67),('Ernestina',107),('Passo Real',64)]:add('ONS',local,'Volume útil',value,'% VU','Até 25/10/2026','observado; referência da fonte',6)
 for local,a,d,pg in [('GBM / Foz do Areia',4603,3837,10),('Salto Santiago',10272,7909,10),('Barra Grande',259,239,13),('Machadinho',935,944,13),('Passo Real',428,266,17)]:
  for ind,value in [('Afluência',a),('Defluência',d)]:add('ONS',local,ind,value,'m³/s','Painel até 25/10/2026','observado',pg)
 for local,value,period,pg,reason in [('Salto Santiago',17000,'PAPC apresentado',9,'ponte BR-158'),('Salto Santiago',19000,'PAPC apresentado',9,'casa de força'),('Passo Real',2400,'PAPC apresentado',16,'UHE Jacuí'),('Dona Francisca',1450,'Novembro a abril',16,'arroz ribeirinho')]:add('ONS',local,'Restrição máxima — '+reason,value,'m³/s',period,'restrição informada; não decisão nova',pg)
 with (out/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow(['instituicao','local','indicador','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf'])
  for r in rows:w.writerow(r[:3]+[str(r[3]).replace('.',',')]+r[4:]+[SITE+'fontes/'+r[0].lower()+'.pdf#page='+str(r[7])])
 # Formal PDF, with shared text/tables, paginated contents and landscape annexes.
 pdfmetrics.registerFont(TTFont('NT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('NTB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'));pdfmetrics.registerFontFamily('NT',normal='NT',bold='NTB',italic='NT',boldItalic='NTB')
 blue=colors.HexColor('#215575');green=colors.HexColor('#166c61')
 st={'body':ParagraphStyle('body',fontName='NT',fontSize=10.2,leading=14.4,spaceAfter=8,alignment=TA_JUSTIFY),'h1':ParagraphStyle('h1',fontName='NTB',fontSize=15,leading=20,spaceAfter=13,textColor=blue,keepWithNext=True),'h2':ParagraphStyle('h2',fontName='NTB',fontSize=11.3,leading=15,spaceBefore=10,spaceAfter=7,textColor=green,keepWithNext=True),'cell':ParagraphStyle('cell',fontName='NT',fontSize=8.3,leading=11),'head':ParagraphStyle('head',fontName='NTB',fontSize=8.3,leading=11,textColor=colors.white),'cover':ParagraphStyle('cover',fontName='NTB',fontSize=22,leading=28,alignment=TA_CENTER,textColor=blue,spaceAfter=18),'center':ParagraphStyle('center',fontName='NT',fontSize=11,leading=16,alignment=TA_CENTER,spaceAfter=12),'caption':ParagraphStyle('caption',fontName='NT',fontSize=9,leading=12,spaceAfter=7)}
 def para(t,k='body'):return Paragraph(t,st[k])
 def inline(el):
  c=BeautifulSoup(str(el),'html.parser')
  for a in c.find_all('a'):a.unwrap()
  return c.find().decode_contents().replace('<strong>','<b>').replace('</strong>','</b>').replace('−','-')
 def table(el,width):
  data=[]
  for i,tr in enumerate(el.find_all('tr')):data.append([para(inline(td),'head' if i==0 else 'cell') for td in tr.find_all(['th','td'])])
  n=len(data[0]);ratios={3:[.27,.33,.4],4:[.24,.23,.27,.26]}.get(n,[1/n]*n)
  t=Table(data,colWidths=[width*r for r in ratios],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),blue),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f6f7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#c4d5dc')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
 def furniture(c,d):
  w,h=c._pagesize;c.saveState();c.setFillColor(colors.HexColor('#566f7b'));c.setFont('NT',7.2);c.drawString(53,h-30,'SOE/ANA — GABINETE | Região Sul — 9ª reunião — 27/10/2026 | PRÉVIA 0.2');c.setStrokeColor(colors.HexColor('#bdcfd7'));c.line(53,h-39,w-53,h-39);c.line(53,54,w-53,54);c.drawCentredString(w/2,40,f'Supervisionado por {NAME} · {ROLE}');c.drawCentredString(w/2,29,'Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)');c.restoreState()
 class Doc(BaseDocTemplate):
  def afterFlowable(self,f):
   if hasattr(f,'toc_key'):
    self.canv.bookmarkPage(f.toc_key);self.canv.addOutlineEntry(f.getPlainText(),f.toc_key,0,False);self.notify('TOCEntry',(0,f.getPlainText(),self.page,f.toc_key))
 ls=landscape(A4);pdfpath=out/'documentos'/PDF;doc=Doc(str(pdfpath),pagesize=A4,title='Nota Técnica preliminar — Região Sul — 27/10/2026',author=NAME+' — '+ROLE+' — SOE/ANA; suporte de IA')
 doc.addPageTemplates([PageTemplate(id='portrait',pagesize=A4,frames=[Frame(56,70,A4[0]-112,A4[1]-120,id='p',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture),PageTemplate(id='landscape',pagesize=ls,frames=[Frame(53,70,ls[0]-106,ls[1]-120,id='l',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture)])
 story=[Spacer(1,30),para('NOTA TÉCNICA<br/>REGIÃO SUL','cover'),para('9ª Reunião em 2026 da Sala de Crise da Região Sul','center'),para('27 de outubro de 2026','center'),Spacer(1,15),para('<b>PRÉVIA TÉCNICA 0.2</b><br/>Consolidação documental em acompanhamento.<br/>Ainda sem registro de encerramento ou deliberações finais.','center'),Spacer(1,20),para('<b>INMET · CEMADEN · ONS · SGB</b>','center'),para(f'Supervisionado por <b>{NAME}</b><br/>{ROLE}<br/>Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA<br/>Elaboração com suporte de inteligência artificial (IA).','center'),Spacer(1,20),para('Tese técnica','h2'),para('A melhora da disponibilidade hídrica coexiste com cheia em curso no Uruguai. A leitura conjunta exige distinguir aporte, estoque, índice de seca, nível local e propagação; as previsões de curto prazo e sazonais não são intercambiáveis.'),para('Protótipo técnico em ambiente pessoal — não constitui publicação institucional da ANA. Não substitui ata, boletim atualizado ou autorização de operação.','caption'),PageBreak(),para('SUMÁRIO','h1')]
 toc=TableOfContents();toc.dotsMinLevel=0;toc.levelStyles=[ParagraphStyle('toc',fontName='NT',fontSize=9.5,leading=14,spaceBefore=6)];story.extend([toc,PageBreak()])
 def heading(text,key):
  h=para(esc(text),'h1');h.toc_key=key;return h
 original=BeautifulSoup(''.join(original_sections.values()),'html.parser')
 def emit(sec,width):
  flow=[]
  for el in sec.children:
   if not getattr(el,'name',None):continue
   if el.name=='h2':continue
   if el.name=='h3':flow.append(para(esc(el.get_text()),'h2'))
   elif el.name=='p':flow.append(para(inline(el)))
   elif el.name=='div' and el.find('table'):flow.extend([table(el.table,width),Spacer(1,10)])
  return flow
 main_ids=['executivo','inmet','cemaden','ons','sgb','cruzamentos','registro','fontes']
 for i,key in enumerate(main_ids):
  if i:story.append(PageBreak())
  sec=original.find(id=key);story.append(heading(sec.h2.get_text(),key));story.extend(emit(sec,A4[0]-112))
 # Annex I uses exactly the same two analytical tables as the website.
 annex=original.find(id='anexo-i');tables=annex.find_all('table');subheads=annex.find_all('h3');annex_flow=[]
 for i,t in enumerate(tables):
  if i:annex_flow.append(PageBreak())
  annex_flow.extend([para('ANEXO I — Resumo para o Relatório Anual / reunião em números','h1'),para(esc(subheads[i].get_text()),'h2'),table(t,ls[0]-106),Spacer(1,10),para('Fontes: INMET, CEMADEN, ONS e SGB, apresentações recebidas para 27/10/2026. Páginas físicas. Observados, parciais e previsões são distintos; este quadro não é estatística anual homologada.','caption')])
 annexpath=out/'documentos'/ANNEX
 SimpleDocTemplate(str(annexpath),pagesize=ls,leftMargin=53,rightMargin=53,topMargin=50,bottomMargin=70,title='Anexo I — Região Sul — prévia',author=NAME).build(annex_flow,onFirstPage=furniture,onLaterPages=furniture)
 story.extend([NextPageTemplate('landscape'),PageBreak(),heading(annex.h2.get_text(),'anexo-i')]);story.extend(emit(annex,ls[0]-106))
 for i,item in enumerate(selected):
  story.append(PageBreak());key=item['key']
  if item==next(f for f in selected if f['key']==key):story.append(heading('ANEXO GRÁFICO — '+LABELS[key],'figuras-'+key))
  story.append(para(f'Figura {item["number"]:02}. {esc(item["title"])}','h2'))
  pix=fitz.Pixmap(out/item['src']);scale=min((ls[0]-110)/pix.width,(ls[1]-235)/pix.height)
  # High-quality JPEG for PDF distribution; original PNG retained on the site.
  jpg=out/'qa'/f'{key}_{item["page"]:02}.jpg';pix.save(jpg,jpg_quality=92)
  im=Image(str(jpg),width=pix.width*scale,height=pix.height*scale);im.hAlign='CENTER';story.extend([im,Spacer(1,7),para(esc(item['caption']),'caption'),para(f'Reprodução original de {LABELS[key]}, p. {item["page"]} do PDF recebido. <link href="{SITE}fontes/{key}.pdf#page={item["page"]}">Consultar fonte integral</link>.','caption')])
 doc.multiBuild(story)
 def paginate(path):
  d=fitz.open(path);n=len(d)
  for i,p in enumerate(d):p.insert_text((p.rect.width-119,p.rect.height-15),f'Página {i+1} de {n}',fontname='helv',fontsize=8,color=(.25,.35,.4))
  tmp=path.with_suffix('.temp.pdf');d.save(tmp,garbage=4,deflate=True);d.close();tmp.replace(path);return n
 pages=paginate(pdfpath);annex_pages=paginate(annexpath)
 d=fitz.open(pdfpath);text=norm(' '.join(p.get_text() for p in d))
 for p in paras:assert p in text,'Missing paragraph: '+p[:120]
 for c in cells:assert c in text,'Missing table cell: '+c[:120]
 assert len(d.get_toc())==13
 for p in d:assert NAME in p.get_text() and ROLE in p.get_text()
 assert sum(len(p.get_images()) for p in d)==32
 for i,p in enumerate(d):p.get_pixmap(matrix=fitz.Matrix(.65,.65),alpha=False).save(out/'qa'/f'page-{i+1:02}.png')
 for i in [0,1]:d[i].get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(out/'qa'/f'cover-toc-{i+1}.png')
 a=fitz.open(annexpath)
 for i,p in enumerate(a):p.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(out/'qa'/f'annex-{i+1}.png')
 manifest={'meeting':'9ª Sala de Crise da Região Sul','date':'2026-10-27','version':'0.2','status':'Prévia técnica — encerramento não informado','generated_at':datetime.now(timezone.utc).isoformat(),'sources':{k:{'sha256':v,'pages':len(fitz.open(source_dir/(k+'.pdf')))} for k,v in HASHES.items()},'pdf_pages':pages,'annex_pages':annex_pages,'figure_count':32,'indicator_rows':len(rows),'pdf_sha256':sha(pdfpath),'annex_sha256':sha(annexpath),'csv_sha256':sha(out/'indicadores.csv'),'figures':selected,'checks':{'all_paragraphs':True,'all_table_cells':True,'credits_every_page':True,'toc_entries':13},'new_web_searches':False,'formal_decisions_received':False}
 (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print('VERIFIED',pages,'pages;',annex_pages,'annex pages;32 figures;',len(rows),'indicator rows.',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--sources',type=Path,required=True);a=ap.parse_args();build(a.output.resolve(),a.sources.resolve())
