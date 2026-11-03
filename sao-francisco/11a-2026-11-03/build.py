#!/usr/bin/env python3
"""São Francisco 11: build from the approved HTML and received, hash-checked PDFs.
No analysis is fetched or inferred by this builder. No other meeting is modified.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, csv, hashlib, html, json, re, shutil
import fitz
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, NextPageTemplate, Image
from reportlab.platypus.tableofcontents import TableOfContents
ROOT=Path(__file__).resolve().parent
SITE='https://7it0.github.io/soe-salas-prototipo/sao-francisco/11a-2026-11-03/'
TITLE='11ª Reunião em 2026 da Sala de Acompanhamento do Sistema Hídrico do Rio São Francisco'
PDF='NT_Sao_Francisco_11a_03-11-2026_CONSOLIDADA.pdf'
ANNEX='Anexo_I_Sao_Francisco_03-11-2026.pdf'
NAME='José Aguiar de Lima Jr.'
ROLE='Especialista em Geoprocessamento'
HASHES={'cemaden':'86db45c42190ba159b2bd62f32483651148ef422d6b46c82db1c2ae5390825ff','ons':'83537d7b2349cc644c991990f5ffcc551ac8bbe32c6d58ca84588d5e75087dad'}
LABELS={'inmet':'INMET','cemaden':'CEMADEN/MCTI','ons':'ONS'}
FIGS={
'cemaden':[
(2,'Chuva acumulada e anomalia em 30 dias','03/10–02/11/2026; leitura espacial, sem estimativa de médias pelas cores.'),
(3,'Situação da estação chuvosa','02/11; critério superior a 3 mm/dia em quatro de cinco dias. Não indica estabelecimento uniforme.'),
(4,'Precipitação na bacia do São Francisco','5,7 mm em 01/11 e 62,7 mm entre 01/10 e 01/11; não são fechamento de novembro.'),
(5,'TSI de longo prazo','Outubro: Xingó −0,44; Sobradinho −0,33; Três Marias −0,24. Condição normal nos três recortes.'),
(6,'TSI de curto prazo','Xingó −0,98 e Sobradinho −1,29: seca moderada. Três Marias 0,09: normal.'),
(7,'Chuva prevista na primeira semana','GEFS, rodada 03/11/2026 00 UTC; acumulado e anomalia são produtos distintos.'),
(8,'Tendência para a segunda semana','Não somar ao acumulado de 14 dias da página seguinte.'),
(9,'Acumulado para duas semanas','Distribuição espacial desigual; os produtos sobrepostos não são aditivos.'),
(10,'GEFS — bacia do São Francisco','Aproximadamente 58 mm em 14 dias; dispersão dos membros preservada.'),
(11,'GEFS — bacia de Sobradinho','Aproximadamente 66 mm em 14 dias; não é vazão afluente.'),
(12,'GEFS — bacia de Três Marias','Aproximadamente 120 mm em 14 dias; não garante recuperação do estoque.'),
(13,'Tendência na terceira e quarta semanas','CFS e ECMWF usam janelas semanais diferentes; preservar datas na comparação.'),
(14,'GloFAS subsazonal','Cabeçalho inicia em 02/10, mas os painéis em 02/11; divergência mantida e registrada.'),
(15,'Contexto ENSO apresentado pelo CEMADEN','Mapa da NOAA reproduzido na apresentação; o destaque +2,5 °C não é tratado como índice trimestral.'),
(16,'Previsão de intensidade ENSO','Produto rotulado como emitido em outubro/2026; não determina impactos locais.'),
(17,'Probabilidades de intensidade de El Niño','Categorias probabilísticas da figura; não equivalem a probabilidades de impactos na bacia.'),
(18,'Previsão sazonal multimodelo de chuva','Novembro–dezembro–janeiro; tendência regional não é cronograma de afluências.'),
(19,'GloFAS sazonal','Novembro e dezembro/2026 e janeiro/2027; categorias de vazão modelada, não defluências operadas.'),
(20,'Anos análogos de El Niño','Trajetórias históricas ilustram dispersão; não comprovam repetição dos impactos.')],
'ons':[
(4,'Afluências dos subsistemas do SIN','Nov./2025–out./2026; panorama hidroenergético não substitui diagnóstico de cada reservatório.'),
(5,'Energia armazenada dos subsistemas','Até 01/11: Nordeste 62%, Norte 61%, Sudeste/Centro-Oeste 55%, Sul 80%. EAR não é VU individual.'),
(6,'Balanço energético dos subsistemas','Composição das fontes; não é uma ordem operativa para a cascata.'),
(7,'Condições hidrológicas e esquema do São Francisco','Coluna final rotulada novembro/2026 precisa de confirmação; 101% e 68% não usados como fechamento mensal.'),
(9,'Três Marias — operação observada','Até 01/11: 69,7% VU; afluência 112 m³/s; defluência 311 m³/s. Rótulos finais, não médias mensais.'),
(10,'Sobradinho — operação observada','Até 01/11: 62,8% VU; afluência 1.150 m³/s; defluência 1.393 m³/s.'),
(11,'Luiz Gonzaga — operação observada','Até 01/11: 37,1% VU; afluência 934 m³/s; defluência 1.056 m³/s.'),
(13,'Três Marias — vazão natural prevista','Média 02/11–31/12: 734 m³/s (89% MLT) e 1.016 m³/s (123%), cenários inferior/superior.'),
(14,'Sobradinho — vazão natural incremental prevista','Média 02/11–31/12: 1.224 m³/s (66% MLT) e 1.510 m³/s (82%). Não é afluência total observada.'),
(16,'Três Marias — premissas de defluência','Inferior: 350/740 m³/s; superior: 430/1.200 m³/s, novembro/dezembro. Simulação, não decisão.'),
(17,'Sobradinho e Xingó — premissas de defluência','Novembro/dezembro: Sobradinho 1.770/1.700 m³/s; Xingó 1.500/1.530 m³/s.'),
(18,'Três Marias — volumes projetados','01/12: 72,9/74,2%; 01/01/2027: 77,1/77,5%, inferior/superior.'),
(19,'Sobradinho — volumes projetados','01/12: 52,5/54,8%; 01/01/2027: 57,5/65,4%. Queda em novembro nos dois cenários.')]
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(t): return html.escape(str(t),quote=True)
def norm(t): return re.sub(r'\s+','',t).replace('−','-').replace('\u00ad','')

def indicators(out):
 rows=[]
 def add(k,local,var,value,unit,period,nature,page,note=''):
  rows.append([LABELS[k],local,var,str(value).replace('.',','),unit,period,nature,str(page),SITE+f'fontes/{k}.pdf#page={page}',note])
 add('cemaden','Bacia do São Francisco','Precipitação',5.7,'mm','01/11/2026','observado_diario',4)
 add('cemaden','Bacia do São Francisco','Precipitação acumulada',62.7,'mm','01/10–01/11/2026','observado_periodo',4,'Intervalo conforme rótulo; não é fechamento de novembro')
 for local,octv,sepv in [('Três Marias',-.24,-.18),('Sobradinho',-.33,-.36),('Xingó',-.44,-.46)]:
  for period,v in [('Outubro/2026',octv),('Setembro/2026',sepv)]:add('cemaden',local,'TSI — longo prazo',v,'adimensional',period,'indice',5,'Normal; janela em meses não explicitada')
 for local,octv,sepv,cl in [('Três Marias',.09,.11,'Normal'),('Sobradinho',-1.29,-1.17,'Seca moderada'),('Xingó',-.98,-.93,'Seca moderada')]:
  for period,v in [('Outubro/2026',octv),('Setembro/2026',sepv)]:add('cemaden',local,'TSI — curto prazo',v,'adimensional',period,'indice',6,cl+'; janela em meses não explicitada')
 for local,v,page in [('Bacia do São Francisco',58,10),('Bacia de Sobradinho',66,11),('Bacia de Três Marias',120,12)]:add('cemaden',local,'GEFS — precipitação em 14 dias',v,'mm','Rodada 03/11/2026 00 UTC','previsao_aproximada',page,'Recortes sobrepostos; não somar')
 for local,vu,qa,qd,page in [('Três Marias',69.7,112,311,9),('Sobradinho',62.8,1150,1393,10),('Luiz Gonzaga',37.1,934,1056,11)]:
  for var,v,u in [('Volume útil',vu,'% VU'),('Afluência',qa,'m³/s'),('Defluência',qd,'m³/s')]:add('ons',local,var,v,u,'Painel até 01/11/2026','observado_painel',page,'Rótulo final; não é média mensal')
 for local,v in [('Nordeste',62),('Norte',61),('Sudeste/Centro-Oeste',55),('Sul',80)]:add('ons','Subsistema '+local,'Energia armazenada',v,'% EARmáx','01/11/2026','observado',5,'Não é volume útil individual')
 for local,v in [('Três Marias',91),('Sobradinho — incremental',74)]:add('ons',local,'Vazão natural relativa',v,'% MLT','Nov.–out. 2025–2026','observado_periodo',7,'MLT 1931–2024; coluna final ambígua excluída')
 for local,lo,hi,lp,hp,page in [('Três Marias',734,1016,89,123,13),('Sobradinho — incremental',1224,1510,66,82,14)]:
  for scen,q,rel in [('inferior',lo,lp),('superior',hi,hp)]:
   add('ons',local,'Vazão natural prevista — '+scen,q,'m³/s','02/11–31/12/2026','cenario_hidrologico',page)
   add('ons',local,'Vazão natural prevista relativa — '+scen,rel,'% MLT','02/11–31/12/2026','cenario_hidrologico',page)
 for local,scen,nov,dec,page in [('Três Marias','inferior',350,740,16),('Três Marias','superior',430,1200,16),('Sobradinho','premissa apresentada',1770,1700,17),('Xingó','premissa apresentada',1500,1530,17)]:
  for period,v in [('Novembro/2026',nov),('Dezembro/2026',dec)]:add('ons',local,'Defluência simulada — '+scen,v,'m³/s',period,'premissa_operativa',page,'Não é mínimo legal nem decisão da reunião')
 for local,date,lo,hi,page in [('Três Marias','01/12/2026',72.9,74.2,18),('Três Marias','01/01/2027',77.1,77.5,18),('Sobradinho','01/12/2026',52.5,54.8,19),('Sobradinho','01/01/2027',57.5,65.4,19)]:
  for scen,v in [('inferior',lo),('superior',hi)]:add('ons',local,'Volume útil previsto — '+scen,v,'% VU',date,'projecao_condicional',page,'Não é intervalo de confiança')
 for local,value in [('Niño 4',0.2),('Niño 3.4',2.5),('Niño 3',3.7),('Niño 1+2',4.6)]:
  add('inmet',local,'Anomalia de TSM apresentada',value,'°C','Quadro apresentado em 03/11/2026','observacao_oceanica_reproduzida',10,'Data de referência própria do produto; não equiparar automaticamente a ONI/RONI')
  rows[-1][8]='Bacia do Rio_SF_INMET_03112026 2.pdf#page=10'
 add('inmet','ENSO / El Niño','Probabilidade de continuidade','>80','%','Até MAM/2027; produto emitido em outubro/2026','previsao_probabilistica',13,'Limiar informado na lâmina; não é probabilidade de impacto local')
 rows[-1][8]='Bacia do Rio_SF_INMET_03112026 2.pdf#page=13'
 assert len(rows)==61
 with (out/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow(['instituicao','local','indicador','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf','observacao']);w.writerows(rows)
 return rows

def build(out):
 out.mkdir(parents=True,exist_ok=True)
 for sub in ['assets','fontes','documentos','qa']:(out/sub).mkdir(exist_ok=True)
 for k,h in HASHES.items():
  source=ROOT/'fontes'/(k+'.pdf');assert sha(source)==h, 'Source differs from received PDF: '+k
  shutil.copyfile(source,out/'fontes'/(k+'.pdf'))
 s=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
 for el in s.select('.gallery,.annex-access,#zoom-script,dialog'):el.decompose()
 originals={sec['id']:BeautifulSoup(str(sec),'html.parser').section for sec in s.select('main > section')}
 assert 'inmet' in originals, 'Vertical INMET ausente'
 sections=list(originals.values())
 paragraphs=[norm(p.get_text(' ',strip=True)) for sec in sections for p in sec.find_all('p')]
 cells=[norm(p.get_text(' ',strip=True)) for sec in sections for p in sec.select('th,td')]
 selected=[]
 for k,figures in FIGS.items():
  source=fitz.open(ROOT/'fontes'/(k+'.pdf'));gallery=s.new_tag('div',attrs={'class':'gallery'})
  for pg,title,caption in figures:
   p=source[pg-1];pix=p.get_pixmap(matrix=fitz.Matrix(1800/p.rect.width,1800/p.rect.width),alpha=False)
   relative=f'assets/{k}_{pg:02}.jpg';pix.pil_save(out/relative,format='JPEG',quality=92,optimize=True)
   number=len(selected)+1;fig=s.new_tag('figure');a=s.new_tag('a',href=relative,attrs={'target':'_blank','rel':'noopener','title':'Ampliar reprodução da apresentação'})
   image=s.new_tag('img',src=relative,alt=f'{LABELS[k]}, página {pg}: {title}',width=str(pix.width),height=str(pix.height),loading='lazy');a.append(image);fig.append(a)
   cap=s.new_tag('figcaption');strong=s.new_tag('strong');strong.string=f'Figura {number} — {title}';cap.append(strong);cap.append(caption)
   span=s.new_tag('span',attrs={'class':'source'});span.string=f'Fonte: {LABELS[k]}, 03/11/2026, página física {pg}. Reprodução original.';cap.append(span)
   link=s.new_tag('a',href=f'fontes/{k}.pdf#page={pg}');link.string='Consultar apresentação';cap.append(link);fig.append(cap);gallery.append(fig)
   selected.append({'number':number,'institution':LABELS[k],'key':k,'page':pg,'title':title,'caption':caption,'src':relative,'width':pix.width,'height':pix.height})
  s.find(id=k).append(gallery);source.close()
 assert len(selected)==32
 rows=indicators(out)
 for ident,href,label in [('pdf-action','documentos/'+PDF,'NT final da reunião · PDF'),('csv-action','indicadores.csv','Dados e indicadores · CSV')]:
  el=s.find(id=ident);assert el is not None;el.name='a';el.attrs={'id':ident,'href':href,'download':''};el.string=label
 p=s.new_tag('p',attrs={'class':'annex-access'});link=s.new_tag('a',href='documentos/'+ANNEX,download='');link.string='Consultar somente o Anexo I · PDF';p.append(link);s.find(id='anexo-i').append(p)
 s.select_one('.notice').string='NT FINAL DA REUNIÃO — versão 1.0 — reunião encerrada, conforme informação do responsável. INMET, CEMADEN e ONS incorporados; atenção às projeções para 2027, conforme manifestação relatada de Joaquim, superintendente da SOE/ANA. Mantidas 32 reproduções de CEMADEN/ONS e 61 indicadores. As imagens e o PDF original do INMET ainda não estão hospedados.'
 for text in list(s.find_all(string=True)):
  if 'prévia documental 0.1' in text.lower():text.replace_with(str(text))
 (out/'index.html').write_text(str(s),encoding='utf-8')
 pdfmetrics.registerFont(TTFont('NT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
 pdfmetrics.registerFont(TTFont('NTB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
 pdfmetrics.registerFontFamily('NT',normal='NT',bold='NTB',italic='NT',boldItalic='NTB')
 blue=colors.HexColor('#215575');green=colors.HexColor('#166c61');ls=landscape(A4)
 st={'body':ParagraphStyle('Body',fontName='NT',fontSize=10,leading=14.6,spaceAfter=9),
 'h1':ParagraphStyle('H1',fontName='NTB',fontSize=16,leading=21,textColor=blue,spaceAfter=12,keepWithNext=True),
 'h2':ParagraphStyle('H2',fontName='NTB',fontSize=11,leading=15,textColor=green,spaceBefore=10,spaceAfter=6,keepWithNext=True),
 'cell':ParagraphStyle('Cell',fontName='NT',fontSize=8.5,leading=11.5),
 'head':ParagraphStyle('Head',fontName='NTB',fontSize=8.5,leading=11.5,textColor=colors.white),
 'caption':ParagraphStyle('Caption',fontName='NT',fontSize=8.5,leading=12,spaceAfter=5),
 'cover':ParagraphStyle('Cover',fontName='NTB',fontSize=24,leading=31,textColor=blue,spaceAfter=22)}
 def para(text,kind='body'):return Paragraph(text,st[kind])
 def inline(el):
  fragment=BeautifulSoup(str(el),'html.parser')
  for tag in fragment.find_all('a'):
   href=tag.get('href','')
   if href.startswith('fontes/'):tag['href']=SITE+href
  return fragment.find().decode_contents().replace('<strong>','<b>').replace('</strong>','</b>').replace('<br>','<br/>')
 def table(el,width):
  data=[]
  for i,tr in enumerate(el.find_all('tr')):data.append([para(esc(c.get_text(' ',strip=True)),'head' if i==0 else 'cell') for c in tr.find_all(['td','th'])])
  n=len(data[0]);ratios={3:[.24,.38,.38],4:[.23,.23,.25,.29],5:[.22,.22,.23,.25,.08]}.get(n,[1/n]*n)
  if n==5 and width<600:ratios=[.23,.14,.19,.19,.25]
  t=Table(data,colWidths=[width*r for r in ratios],repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),blue),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cad9df')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7f8')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));return t
 def emit(sec,width):
  result=[]
  for el in sec.children:
   if not getattr(el,'name',None):continue
   if el.name=='h3':result.append(para(esc(el.get_text()),'h2'))
   elif el.name=='p':result.append(para(inline(el)))
   elif el.name=='div' and 'tablewrap' in el.get('class',[]):result.extend([table(el.table,width),Spacer(1,9)])
  return result
 def furniture(c,doc):
  w,h=c._pagesize;c.saveState();c.setFont('NT',7);c.setFillColor(colors.HexColor('#506975'));c.drawString(52,h-28,'SOE/ANA — GABINETE | SÃO FRANCISCO | 11ª reunião — 03/11/2026 | Consolidação 1.0');c.setStrokeColor(colors.HexColor('#bfd1da'));c.line(52,h-35,w-52,h-35);c.line(52,57,w-52,57)
  c.drawCentredString(w/2,43,'Supervisionado por '+NAME+' · '+ROLE);c.drawCentredString(w/2,32,'Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)');c.drawCentredString(w/2,22,'Discussão interna · Protótipo pessoal — não constitui publicação institucional da ANA.');c.restoreState()
 class Doc(BaseDocTemplate):
  def afterFlowable(self,f):
   if hasattr(f,'toc_key'):
    self.canv.bookmarkPage(f.toc_key);self.canv.addOutlineEntry(f.getPlainText(),f.toc_key,0,False);self.notify('TOCEntry',(0,f.getPlainText(),self.page,f.toc_key))
 def heading(text,key):
  p=para(esc(text),'h1');p.toc_key=key;return p
 pdfpath=out/'documentos'/PDF
 doc=Doc(str(pdfpath),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=52,bottomMargin=74,title=TITLE,author=NAME)
 doc.addPageTemplates([PageTemplate(id='portrait',pagesize=A4,frames=[Frame(56,74,A4[0]-112,A4[1]-126,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture),PageTemplate(id='landscape',pagesize=ls,frames=[Frame(53,74,ls[0]-106,ls[1]-126,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture)])
 story=[Spacer(1,32),para(esc(TITLE),'cover'),para('Nota Técnica — SÃO FRANCISCO','h1'),para('3 de novembro de 2026 · Consolidação pós-reunião 1.0','h2'),Spacer(1,12),para('Condições hidrológicas, transição para o período chuvoso e perspectivas de operação da cascata.'),Spacer(1,18),para('<b>Supervisionado por '+NAME+'</b>'),para(ROLE+'<br/>Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA'),para('Elaboração com suporte de inteligência artificial (IA).'),Spacer(1,18),para('Base: INMET, 18 páginas; CEMADEN e ONS, 20 páginas cada. As três apresentações foram recebidas e analisadas. Encerramento confirmado; preocupação com as projeções para 2027 registrada. Não foram comunicadas novas deliberações operativas. As 32 reproduções são do CEMADEN e do ONS; as imagens do INMET ainda não integram esta edição.'),para('Três verticais completas, cruzamentos, quadro executivo, Anexo I, 32 reproduções identificadas de CEMADEN/ONS e base de 61 indicadores.'),PageBreak(),para('SUMÁRIO','h1')]
 toc=TableOfContents();toc.levelStyles=[ParagraphStyle('Toc',fontName='NT',fontSize=9,leading=14,spaceBefore=7)];story.extend([toc,PageBreak()])
 keys=['executivo','escopo','inmet','cemaden','ons','cruzamentos','acompanhamento','registro','fontes']
 for i,key in enumerate(keys):
  if i:story.append(PageBreak())
  sec=originals[key];story.append(heading(sec.h2.get_text(),key));story.extend(emit(sec,A4[0]-112))
 annex=originals['anexo-i'];blocks=annex.select('.annex-block');assert len(blocks)==5
 story.extend([NextPageTemplate('landscape'),PageBreak(),heading(annex.h2.get_text(),'anexo-i')]);story.extend(emit(annex,ls[0]-106))
 separate=[para(esc(annex.h2.get_text()),'h1')]+emit(annex,ls[0]-106)
 for i,block in enumerate(blocks):
  if i:story.append(PageBreak());separate.append(PageBreak())
  story.extend(emit(block,ls[0]-106));separate.extend(emit(block,ls[0]-106))
 annexpath=out/'documentos'/ANNEX
 SimpleDocTemplate(str(annexpath),pagesize=ls,leftMargin=53,rightMargin=53,topMargin=52,bottomMargin=74,title='Anexo I — São Francisco — 03/11/2026',author=NAME).build(separate,onFirstPage=furniture,onLaterPages=furniture)
 seen=set()
 for f in selected:
  story.append(PageBreak());k=f['key']
  if k not in seen:story.append(heading('ANEXO GRÁFICO — '+LABELS[k],'figuras-'+k));seen.add(k)
  story.append(para('Figura '+str(f['number']).zfill(2)+' — '+esc(f['title']),'h2'))
  scale=min((ls[0]-114)/f['width'],(ls[1]-238)/f['height']);im=Image(str(out/f['src']),width=f['width']*scale,height=f['height']*scale);im.hAlign='CENTER'
  story.extend([im,Spacer(1,8),para(esc(f['caption']),'caption'),para(f'Fonte: {LABELS[k]}, apresentação de 03/11/2026, página física {f["page"]}. Reprodução original. <link href="{SITE}fontes/{k}.pdf#page={f["page"]}">Consultar fonte integral.</link>','caption')])
 doc.multiBuild(story)
 def paginate(path):
  d=fitz.open(path);total=len(d)
  for i,p in enumerate(d):p.insert_text((p.rect.width-125,p.rect.height-11),f'Página {i+1} de {total}',fontsize=8,fontname='helv',color=(.25,.35,.4))
  tmp=path.with_suffix('.tmp.pdf');d.save(tmp,garbage=4,deflate=True);d.close();tmp.replace(path);return total
 pages=paginate(pdfpath);annpages=paginate(annexpath)
 d=fitz.open(pdfpath);fulltext=norm(' '.join(p.get_text(clip=fitz.Rect(45,48,p.rect.width-45,p.rect.height-70)) for p in d))
 for text in paragraphs:assert text in fulltext,'Paragraph missing: '+text[:160]
 for text in cells:assert text in fulltext,'Table cell missing: '+text[:160]
 assert len(d.get_toc())==12
 assert sum(len(p.get_images()) for p in d)==32
 for p in d:
  text=p.get_text();assert NAME in text and ROLE in text and 'inteligência artificial' in text
 for i,p in enumerate(d):p.get_pixmap(matrix=fitz.Matrix(.7,.7),alpha=False).save(out/'qa'/f'page-{i+1:02}.png')
 for i in [0,1,2]:d[i].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(out/'qa'/f'check-{i+1:02}.png')
 ad=fitz.open(annexpath)
 for i,p in enumerate(ad):p.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(out/'qa'/f'annex-{i+1}.png')
 manifest={'meeting':TITLE,'date':'2026-11-03','version':'1.0','status':'Consolidação pós-reunião; três verticais incorporadas; encerramento confirmado; preocupação relatada com 2027; imagens INMET não hospedadas','generated_at':datetime.now(timezone.utc).isoformat(),'sources':{k:{'sha256':h,'pages':20,'matches_received_file':True} for k,h in HASHES.items()},'pdf_pages':pages,'annex_pages':annpages,'figure_count':32,'indicator_rows':61,'pdf_sha256':sha(pdfpath),'annex_sha256':sha(annexpath),'csv_sha256':sha(out/'indicadores.csv'),'toc':d.get_toc(),'figures':selected,'checks':{'all_paragraphs':True,'all_table_cells':True,'credits_every_page':True,'reserved_image_dimensions':True},'formal_decisions_received':False}
 manifest['status']='Consolidação pós-reunião; encerramento confirmado; atenção às projeções para 2027; original e imagens INMET ainda não hospedados'
 manifest['meeting_closed']=True
 manifest['closure_source']='Relato do responsável pelo acompanhamento em 03/11/2026'
 manifest['closure_focus']='Preocupação de Joaquim, superintendente da SOE/ANA, com as projeções e o comportamento do sistema hídrico em 2027, conforme relato do usuário.'
 manifest['new_operational_decisions_reported']=False
 manifest['pdf_path']='documentos/'+PDF
 manifest['sources']['inmet']={'sha256':'c7eafb4527008b52839e02058da2b3bba29a0c02893482886745ce198680aee9','pages':18,'received_and_analyzed':True,'original_pdf_hosted':False,'figures_hosted':False}
 (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 email='Assunto: São Francisco — 11ª reunião de 2026 — consolidação pós-reunião\n\nPrezados(as),\n\nCompartilho a página da reunião de 03/11/2026: '+SITE+'\n\nO endereço reúne as verticais INMET, CEMADEN e ONS, cruzamentos, NT integral em PDF, Anexo I e indicadores. A análise do INMET integra esta revisão; as reproduções gráficas do INMET ainda não estão hospedadas. Reunião encerrada. Conforme relato do responsável, Joaquim, superintendente da SOE/ANA, destacou preocupação com as projeções para 2027. Não foram comunicadas novas deliberações operativas.\n\nAtenciosamente,\n'+NAME+'\n'+ROLE+' — Gabinete/SOE/ANA\n'
 (out/'email_encaminhamento.txt').write_text(email,encoding='utf-8')
 print('VERIFIED:',pages,'NT pages;',annpages,'annex pages;32 figures;61 indicators.',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.output.resolve())
