#!/usr/bin/env python3
"""Tocantins 10a: same analytical text in HTML/PDF; verified received sources.
No institutional decisions are invented. Previous meeting folders are untouched.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,hashlib,html,json,re,shutil
import fitz
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,SimpleDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,PageBreak,NextPageTemplate,Image,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
ROOT=Path(__file__).resolve().parent
SITE='https://7it0.github.io/soe-salas-prototipo/tocantins/10a-2026-10-27/'
TITLE='10ª Reunião em 2026 da Sala de Acompanhamento do Sistema Hídrico do Rio Tocantins'
PDF='NT_Tocantins_10a_27-10-2026_PREVIA.pdf'
ANNEX='Anexo_I_Tocantins_27-10-2026_PREVIA.pdf'
NAME='José Aguiar de Lima Jr.'
ROLE='Especialista em Geoprocessamento'
LABELS={'cemaden':'CEMADEN','ons':'ONS'}
HASHES={'cemaden':'e0d660058def8d84b03c168399bf2b0250671a10c5a6fd49b78f7f941b4acaf4','ons':'b0fa096f74332a58da11139fc5f2ce5e89152d42e6686a7bbb2bb182740867d7'}
FIGS={
'cemaden':[(2,'Chuva acumulada e anomalia em 30 dias','26/09 a 26/10; distribuição espacial desigual no sistema.'),(3,'Situação da estação chuvosa','Critério superior a 3 mm/dia em quatro de cinco dias; não representa estabelecimento homogêneo em toda a bacia.'),(4,'Precipitação na bacia do Tocantins','56,3 mm entre 1 e 26/10. Não é fechamento mensal.'),(5,'Precipitação na bacia do Araguaia','87,2 mm entre 1 e 26/10; recorte distinto do Tocantins.'),(6,'Serra da Mesa — precipitação e vazão','Outubro até 25/10: 79 mm e média de 102 m³/s; valor diário de 72 m³/s em 25/10. MLT 1983–2025.'),(7,'TSI de longo prazo — Tocantins','Tucuruí −1,45; Descarreto −1,31; Serra da Mesa −1,39. Classes de seca severa preservadas.'),(8,'TSI de longo prazo — Araguaia','Araguatins −1,40; Conceição do Araguaia −1,49; seca severa.'),(10,'GEFS — bacia do Tocantins','Cerca de 42 mm em 14 dias, rodada de 27/10 00 UTC; preservar a dispersão.'),(11,'GEFS — bacia do Araguaia','Cerca de 41 mm em 14 dias; maiores acumulados em parcelas meridionais.'),(12,'GEFS — Baixo Tocantins','Cerca de 11 mm em 14 dias; não confundir com o sinal previsto no alto curso.'),(13,'GEFS — Serra da Mesa','Cerca de 88 mm em 14 dias; é previsão, não precipitação verificada.'),(14,'PDM-CEMADEN — previsão de 14 dias','250 m³/s em 26/10–08/11: 105% da MLT de outubro, mas 55% da de novembro.'),(16,'Previsão de vazão natural — Tocantins–Araguaia','24/10 a 23/11; trajetórias e incertezas próprias deste produto.'),(17,'GloFAS subsazonal','Categorias de vazão e incerteza até 07/12; não equivalem a defluências operadas.'),(21,'Previsão sazonal de chuva multimodelo','Novembro–dezembro–janeiro; tendência regional, não cronograma diário de afluências.'),(22,'GloFAS sazonal — Tocantins','Rótulo original DNJ preservado; sequência interpretada pelo contexto como nov./dez. de 2026 e jan. de 2027.'),(24,'Serra da Mesa — sensibilidade PDM','Linhas não são percentis. Rótulo Pcrítica (2015/2026) preservado. Curva −50% sem linha numérica própria.')],
'ons':[(5,'Energia armazenada dos subsistemas','Até 25/10: Nordeste 62%, Norte 63%, Sudeste 55% e Sul 83%; EAR não é VU individual.'),(8,'Serra da Mesa — vazões naturais','Outubro parcial até 25/10 em 34% da MLT, base 1931–2024.'),(9,'Estreito — vazões naturais','Outubro parcial até 25/10 em 52% da MLT, base 1931–2024.'),(10,'Tucuruí — vazões naturais','Dados até 26/10; não foi convertido em número exato um ponto sem rótulo explícito.'),(12,'Cascata, tempos de viagem e mínimos informados','Serra da Mesa 43% VU e Tucuruí 59% no diagrama. Mínimos médios e instantâneos são distintos.'),(13,'Serra da Mesa — operação','43% VU e defluência final de 743 m³/s; nenhum valor exato de afluência final foi inferido da curva.'),(14,'Estreito — operação','2.244 m³/s afluentes, 1.580 m³/s defluentes e nível de 155,52 m; painel até 25/10.'),(15,'Tucuruí — operação','1.663 m³/s afluentes, 4.436 m³/s defluentes e 60% VU no painel; divergência com 59% do diagrama preservada.'),(17,'Premissas da simulação de Serra da Mesa','27/10–30/11; SMAP/ONS–ECMWF; 1.040 m³/s seg.–sáb. e 720 m³/s domingos/feriados. Não são decisões novas.'),(18,'Serra da Mesa — afluência do cenário','Média de 162 m³/s e 32% MLT informada na tabela. Harmonizar janela antes de comparar ao PDM.'),(19,'Serra da Mesa — armazenamento projetado','43% observado para 37% no horizonte da simulação até 30/11; resultado condicional.')]
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(t):return html.escape(str(t),quote=True)
def norm(t):return re.sub(r'\s+','',t).replace('−','-').replace('\u00ad','')

def indicators(out):
 rows=[]
 def add(k,local,var,v,u,period,nature,p,note=''):
  rows.append([LABELS[k],local,var,str(v).replace('.',','),u,period,nature,str(p),SITE+f'fontes/{k}.pdf#page={p}',note])
 for local,v,p in [('Bacia Tocantins',56.3,4),('Bacia Araguaia',87.2,5)]:add('cemaden',local,'Precipitação acumulada',v,'mm','01–26/10/2026','observado_parcial',p)
 for var,v,u in [('Precipitação outubro',79,'mm'),('Precipitação relativa',64,'% MLT'),('Vazão média outubro',102,'m³/s'),('Vazão média relativa',43,'% MLT')]:add('cemaden','Serra da Mesa',var,v,u,'Outubro até 25/10/2026','observado_parcial',6,'MLT 1983–2025')
 for var,v,u in [('Vazão diária',72,'m³/s'),('Vazão diária relativa',30,'% MLT')]:add('cemaden','Serra da Mesa',var,v,u,'25/10/2026','observado_diario',6,'Referência apresentada pelo CEMADEN')
 for period,rain,pr,q,pq in [('Out/2025–abr/2026',1260,91,622,68),('Mai–set/2026',46,46,193,66)]:
  for var,v,u in [('Precipitação',rain,'mm'),('Precipitação relativa',pr,'% MLT'),('Vazão média',q,'m³/s'),('Vazão relativa',pq,'% MLT')]:add('cemaden','Serra da Mesa',var,v,u,period,'observado_periodo',6)
 for local,v,p in [('Tucuruí',-1.45,7),('Descarreto',-1.31,7),('Serra da Mesa',-1.39,7),('Araguatins',-1.40,8),('Conceição do Araguaia',-1.49,8)]:add('cemaden',local,'TSI-12',v,'adimensional','Outubro/2026 parcial','indice_acumulado',p,'Seca hidrológica severa na fonte')
 for local,v,p in [('Tocantins',42,10),('Araguaia',41,11),('Baixo Tocantins',11,12),('Serra da Mesa',88,13)]:add('cemaden',local,'Chuva GEFS acumulada em 14 dias',v,'mm','Rodada 27/10/2026 00 UTC','previsao_aproximada',p)
 for var,v,u in [('Vazão média PDM',250,'m³/s'),('Vazão PDM relativa à MLT outubro',105,'% MLT'),('Vazão PDM relativa à MLT novembro',55,'% MLT')]:add('cemaden','Serra da Mesa',var,v,u,'26/10–08/11/2026','previsao',14)
 for scen,q1,p1,q2,p2 in [('+25% Média',828,117,2042,160),('Linha cinza sem rótulo inequívoco',611,87,1224,96),('−25% Média',422,60,700,55),('Pcrítica (2015/2026), rótulo da fonte',261,37,722,57)]:
  for period,q,pct in [('Nov–dez/2026',q1,p1),('Jan–mar/2027',q2,p2)]:
   add('cemaden','Serra da Mesa','PDM — '+scen,q,'m³/s',period,'cenario_sensibilidade',24,'Não é percentil nem decisão; identificação pela cor do quadro')
   add('cemaden','Serra da Mesa','PDM relativo — '+scen,pct,'% MLT',period,'cenario_sensibilidade',24)
 for local,v in [('Nordeste',62),('Norte',63),('Sudeste/Centro-Oeste',55),('Sul',83)]:add('ons','Subsistema '+local,'Energia armazenada',v,'% EARmáx','25/10/2026','observado',5,'Não é volume útil individual')
 for local,v,p in [('Serra da Mesa',34,8),('Estreito',52,9)]:add('ons',local,'Vazão natural relativa',v,'% MLT','Outubro parcial até 25/10/2026','observado_parcial',p,'MLT 1931–2024')
 for local,var,v,u,p in [('Serra da Mesa','Volume útil',43,'% VU',13),('Serra da Mesa','Defluência',743,'m³/s',13),('Estreito','Afluência',2244,'m³/s',14),('Estreito','Defluência',1580,'m³/s',14),('Estreito','Nível de montante',155.52,'m',14),('Tucuruí','Afluência',1663,'m³/s',15),('Tucuruí','Defluência',4436,'m³/s',15),('Tucuruí','Volume útil — painel',60,'% VU',15),('Tucuruí','Volume útil — diagrama',59,'% VU',12)]:add('ons',local,var,v,u,'Painel / referência de 25/10/2026','observado',p,'Valores finais; divergência 59/60% de Tucuruí preservada' if local=='Tucuruí' else '')
 for var,v,u,p,period in [('Defluência média seg.–sáb.',1040,'m³/s',17,'27/10–30/11/2026'),('Defluência média dom./feriados',720,'m³/s',17,'27/10–30/11/2026'),('Afluência média prevista',162,'m³/s',18,'Lâmina do cenário ONS'),('Afluência média prevista relativa',32,'% MLT',18,'Lâmina do cenário ONS'),('Volume útil final previsto',37,'% VU',19,'Até 30/11/2026')]:add('ons','Serra da Mesa',var,v,u,period,'premissa_simulacao' if p==17 else 'projecao_condicional',p,'Não é decisão nova')
 for local,var,v,period in [('Serra da Mesa','Mínimo médio diário',100,'Dezembro–maio'),('Serra da Mesa','Mínimo médio diário',300,'Junho–novembro'),('Serra da Mesa','Mínimo instantâneo declarado',300,'Junho–novembro'),('Cana Brava','Mínimo indicado',90,'Conforme diagrama'),('São Salvador','Mínimo indicado',90,'Conforme diagrama'),('Peixe Angical','Mínimo indicado',360,'Conforme diagrama'),('Lajeado','Mínimo indicado',255,'Conforme diagrama'),('Estreito','Mínimo atribuído ao IBAMA',744,'Conforme diagrama')]:add('ons',local,var,v,'m³/s',period,'restricao_informada',12,'Condições integrais não auditadas; não é deliberação desta reunião')
 with (out/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow(['instituicao','local','indicador','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf','observacao']);w.writerows(rows)
 return rows

def build(out,sources):
 out.mkdir(parents=True,exist_ok=True)
 for sub in ['assets','fontes','documentos','qa']:(out/sub).mkdir(exist_ok=True)
 for key,h in HASHES.items():
  src=sources/(key+'.pdf');assert sha(src)==h,'Different from received source: '+key
  if src.resolve()!=(out/'fontes'/(key+'.pdf')).resolve():shutil.copyfile(src,out/'fontes'/(key+'.pdf'))
 s=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
 # Rebuilding uses the analytical source only; galleries and generated links are replaced.
 for el in s.select('.gallery,.source-access,.annex-access,dialog,#zoom-script'):el.decompose()
 sections=list(s.select('main > section'));paras=[norm(p.get_text(' ',strip=True)) for sec in sections for p in sec.find_all('p')];cells=[norm(e.get_text(' ',strip=True)) for sec in sections for e in sec.select('th,td')]
 original={sec['id']:BeautifulSoup(str(sec),'html.parser').section for sec in sections}
 selected=[]
 for key,figs in FIGS.items():
  src=fitz.open(sources/(key+'.pdf'));gallery=s.new_tag('div',attrs={'class':'gallery'})
  for pg,title,caption in figs:
   n=len(selected)+1;p=src[pg-1];pix=p.get_pixmap(matrix=fitz.Matrix(1800/p.rect.width,1800/p.rect.width),alpha=False)
   relative=f'assets/{key}_{pg:02}.png';pix.save(out/relative)
   jpg=out/'qa'/f'{key}_{pg:02}.jpg';pix.save(jpg,jpg_quality=93)
   item={'number':n,'key':key,'institution':LABELS[key],'page':pg,'title':title,'caption':caption,'src':relative,'width':pix.width,'height':pix.height};selected.append(item)
   fig=BeautifulSoup(f'<figure id="fig-{n:02}"><a href="{relative}" data-zoom="{relative}"><img src="{relative}" width="{pix.width}" height="{pix.height}" alt="{esc(title)}" loading="lazy"></a><figcaption><strong>Figura {n:02} — {esc(title)}</strong>{esc(caption)}<span class="source">Fonte: {LABELS[key]}, apresentação de 27/10/2026, p. {pg} do PDF recebido. Reprodução original.</span><a href="fontes/{key}.pdf#page={pg}" target="_blank" rel="noopener">Consultar apresentação</a></figcaption></figure>','html.parser').figure;gallery.append(fig)
  s.find(id=key).append(gallery);src.close()
 assert len(selected)==28
 s.select_one('.notice').string='PRÉVIA TÉCNICA 0.2 — duas verticais completas, cruzamentos, Anexo I e 28 reproduções identificadas. INMET ainda não recebido; encerramento e deliberações finais não informados.'
 s.select_one('.actions').clear();actions=BeautifulSoup(f'<a href="#executivo">Ler NT — versão navegável</a><a href="documentos/{PDF}" download>Nota Técnica integral · PDF preliminar</a><div class="data-actions"><a href="indicadores.csv" download>Dados e indicadores · CSV</a><a href="#anexo-i">Anexo I — Reunião em números</a></div>','html.parser')
 for el in list(actions.contents):s.select_one('.actions').append(el)
 links=s.new_tag('p',attrs={'class':'source-access'})
 for key,label in LABELS.items():
  a=s.new_tag('a',href=f'fontes/{key}.pdf',target='_blank',rel='noopener');a.string=label+' — apresentação integral';links.append(a);links.append(' · ')
 s.find(id='fontes').append(links)
 s.find(id='anexo-i').append(BeautifulSoup(f'<p class="annex-access"><a href="documentos/{ANNEX}" download>Anexo I — PDF para consulta e encaminhamento</a></p>','html.parser').p)
 s.select_one('footer > p').string='27/10/2026 · Prévia 0.2 · Dois PDFs recebidos; reunião em acompanhamento.'
 dialog=BeautifulSoup('<dialog id="zoom"><button type="button">Fechar ×</button><img alt="Reprodução ampliada"></dialog>','html.parser').dialog;s.body.append(dialog)
 js=s.new_tag('script',id='zoom-script');js.string="const d=document.querySelector('#zoom');document.querySelectorAll('[data-zoom]').forEach(a=>a.onclick=e=>{if(!d.showModal)return;e.preventDefault();d.querySelector('img').src=a.dataset.zoom;d.showModal();});d.querySelector('button').onclick=()=>d.close();d.onclick=e=>{if(e.target===d)d.close();};";s.body.append(js)
 # Width and height attributes reserve figure space and prevent hash jumps while lazy images load.
 (out/'index.html').write_text(str(s),encoding='utf-8');rows=indicators(out)
 pdfmetrics.registerFont(TTFont('NT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('NTB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'));pdfmetrics.registerFontFamily('NT',normal='NT',bold='NTB',italic='NT',boldItalic='NTB')
 blue=colors.HexColor('#215575');green=colors.HexColor('#166c61');ls=landscape(A4)
 st={'body':ParagraphStyle('Body',fontName='NT',fontSize=9.5,leading=14,spaceAfter=8),'h1':ParagraphStyle('H1',fontName='NTB',fontSize=16,leading=20,textColor=blue,spaceBefore=5,spaceAfter=12,keepWithNext=True),'h2':ParagraphStyle('H2',fontName='NTB',fontSize=11,leading=15,textColor=green,spaceBefore=12,spaceAfter=6,keepWithNext=True),'cell':ParagraphStyle('Cell',fontName='NT',fontSize=8,leading=11),'head':ParagraphStyle('Head',fontName='NTB',fontSize=8,leading=11,textColor=colors.white),'caption':ParagraphStyle('Caption',fontName='NT',fontSize=8.5,leading=12,spaceAfter=5),'cover':ParagraphStyle('Cover',fontName='NTB',fontSize=24,leading=31,textColor=blue,spaceAfter=22)}
 def para(text,kind='body'):return Paragraph(text,st[kind])
 def inline(el):
  t=el.decode_contents().replace('<strong>','<b>').replace('</strong>','</b>').replace('<br>','<br/>')
  return t
 def table(el,width):
  trs=el.find_all('tr');data=[]
  for i,tr in enumerate(trs):data.append([para(esc(c.get_text(' ',strip=True)),'head' if i==0 else 'cell') for c in tr.find_all(['td','th'])])
  n=len(data[0]);widths=[width/n]*n
  if n==4:widths=[width*.24,width*.23,width*.24,width*.29]
  if n==3:widths=[width*.36,width*.32,width*.32]
  t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),blue),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cad9df')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7f8')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));return t
 def furniture(c,doc):
  w,h=c._pagesize;c.saveState();c.setFont('NT',7);c.setFillColor(colors.HexColor('#506975'));c.drawString(52,h-28,'SOE/ANA — GABINETE | TOCANTINS | 10ª reunião — 27/10/2026 | Prévia 0.2');c.setStrokeColor(colors.HexColor('#bfd1da'));c.line(52,h-35,w-52,h-35);c.line(52,57,w-52,57)
  c.drawCentredString(w/2,43,'Supervisionado por '+NAME+' · '+ROLE);c.drawCentredString(w/2,32,'Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)');c.drawCentredString(w/2,22,'Protótipo técnico em ambiente pessoal — não constitui publicação institucional da ANA.');c.restoreState()
 class Doc(BaseDocTemplate):
  def afterFlowable(self,f):
   if hasattr(f,'toc_key'):
    self.canv.bookmarkPage(f.toc_key);self.canv.addOutlineEntry(f.getPlainText(),f.toc_key,0,False);self.notify('TOCEntry',(0,f.getPlainText(),self.page,f.toc_key))
 def heading(text,key):
  p=para(esc(text),'h1');p.toc_key=key;return p
 def emit(sec,width):
  result=[]
  for el in sec.children:
   if not getattr(el,'name',None):continue
   if el.name=='h3':result.append(para(esc(el.get_text()),'h2'))
   elif el.name=='p':result.append(para(inline(el)))
   elif el.name=='div' and el.find('table'):result.extend([table(el.table,width),Spacer(1,9)])
  return result
 pdfpath=out/'documentos'/PDF
 doc=Doc(str(pdfpath),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=52,bottomMargin=74,title=TITLE,author=NAME)
 doc.addPageTemplates([PageTemplate(id='portrait',pagesize=A4,frames=[Frame(56,74,A4[0]-112,A4[1]-126,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture),PageTemplate(id='landscape',pagesize=ls,frames=[Frame(53,74,ls[0]-106,ls[1]-126,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=furniture)])
 story=[Spacer(1,44),para(esc(TITLE),'cover'),para('Nota Técnica — TOCANTINS','h1'),para('27 de outubro de 2026 · Prévia técnica 0.2','h2'),Spacer(1,16),para('Seca hidrológica persistente, recuperação de afluências e deplecionamento condicionado dos reservatórios.'),Spacer(1,24),para('<b>Supervisionado por '+NAME+'</b>'),para(ROLE+'<br/>Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA'),para('Elaboração com suporte de inteligência artificial (IA).'),Spacer(1,28),para('Base documental: CEMADEN (24 páginas) e ONS (20 páginas), arquivos recebidos. INMET ainda não recebido. Não há registro de encerramento ou deliberação final nesta edição.'),para('Contém duas verticais, cruzamentos, Anexo I de síntese numérica e 28 reproduções das fontes.'),PageBreak(),para('SUMÁRIO','h1')]
 toc=TableOfContents();toc.levelStyles=[ParagraphStyle('Toc',fontName='NT',fontSize=9,leading=14,leftIndent=0,firstLineIndent=0,spaceBefore=7)];story.extend([toc,PageBreak()])
 for i,key in enumerate(['executivo','escopo','cemaden','ons','cruzamentos','operacao','registro','fontes']):
  if i:story.append(PageBreak())
  sec=original[key];story.append(heading(sec.h2.get_text(),key));story.extend(emit(sec,A4[0]-112))
 annex=original['anexo-i'];story.extend([NextPageTemplate('landscape'),PageBreak(),heading(annex.h2.get_text(),'anexo-i')]);story.extend(emit(annex,ls[0]-106))
 # Same complete numerical annex, separately downloadable.
 annexpath=out/'documentos'/ANNEX
 SimpleDocTemplate(str(annexpath),pagesize=ls,leftMargin=53,rightMargin=53,topMargin=52,bottomMargin=74,title='Anexo I — Tocantins — 27/10/2026',author=NAME).build([para(esc(annex.h2.get_text()),'h1')]+emit(annex,ls[0]-106),onFirstPage=furniture,onLaterPages=furniture)
 seen=set()
 for item in selected:
  story.append(PageBreak());key=item['key']
  if key not in seen:story.append(heading('ANEXO GRÁFICO — '+LABELS[key],'figuras-'+key));seen.add(key)
  story.append(para('Figura '+str(item['number']).zfill(2)+' — '+esc(item['title']),'h2'))
  scale=min((ls[0]-114)/item['width'],(ls[1]-238)/item['height']);im=Image(str(out/'qa'/f'{key}_{item["page"]:02}.jpg'),width=item['width']*scale,height=item['height']*scale);im.hAlign='CENTER'
  story.extend([im,Spacer(1,8),para(esc(item['caption']),'caption'),para(f'Fonte: {LABELS[key]}, apresentação de 27/10/2026, página {item["page"]} do PDF recebido. Reprodução original. <link href="{SITE}fontes/{key}.pdf#page={item["page"]}">Consultar fonte integral.</link>','caption')])
 doc.multiBuild(story)
 def paginate(path):
  d=fitz.open(path);total=len(d)
  for i,p in enumerate(d):p.insert_text((p.rect.width-125,p.rect.height-11),f'Página {i+1} de {total}',fontsize=8,fontname='helv',color=(.25,.35,.4))
  tmp=path.with_suffix('.tmp.pdf');d.save(tmp,garbage=4,deflate=True);d.close();tmp.replace(path);return total
 pages=paginate(pdfpath);annpages=paginate(annexpath)
 d=fitz.open(pdfpath);text=norm(' '.join(p.get_text() for p in d))
 for p in paras:assert p in text,'Paragraph missing: '+p[:120]
 for cell in cells:assert cell in text,'Cell missing: '+cell[:120]
 assert len(d.get_toc())==11
 for p in d:assert NAME in p.get_text() and ROLE in p.get_text() and 'inteligência artificial' in p.get_text()
 assert sum(len(p.get_images()) for p in d)==28
 for i,p in enumerate(d):p.get_pixmap(matrix=fitz.Matrix(.65,.65),alpha=False).save(out/'qa'/f'page-{i+1:02}.png')
 for i in [0,1]:d[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(out/'qa'/f'cover-toc-{i+1}.png')
 ad=fitz.open(annexpath)
 for i,p in enumerate(ad):p.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(out/'qa'/f'annex-{i+1}.png')
 manifest={'meeting':TITLE,'date':'2026-10-27','version':'0.2','status':'Prévia documental; INMET não recebido; encerramento não informado','generated_at':datetime.now(timezone.utc).isoformat(),'sources':{k:{'sha256':h,'pages':len(fitz.open(sources/(k+'.pdf'))),'matches_received_file':True} for k,h in HASHES.items()},'pdf_pages':pages,'annex_pages':annpages,'figure_count':28,'indicator_rows':len(rows),'pdf_sha256':sha(pdfpath),'annex_sha256':sha(annexpath),'csv_sha256':sha(out/'indicadores.csv'),'toc':d.get_toc(),'figures':selected,'checks':{'all_paragraphs':True,'all_table_cells':True,'credits_every_page':True,'reserved_image_dimensions':True},'formal_decisions_received':False,'source_of_analysis':'PDFs enviados pelo responsável; cópias de publicação verificadas por SHA-256'}
 (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print('VERIFIED',pages,'PDF pages;',annpages,'annex pages;28 figures;',len(rows),'indicator records.',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--sources',type=Path,required=True);a=ap.parse_args();build(a.output.resolve(),a.sources.resolve())
