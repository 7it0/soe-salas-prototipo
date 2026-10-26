#!/usr/bin/env python3
"""Add Anexo I from the approved indicators; preserve analysis, figures and CSV."""
from pathlib import Path
import argparse,csv,hashlib,html,io,json,re,shutil
import fitz
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak
PDF='NT_Paranapanema_10a_22-10-2026.pdf'
ANNEX='Anexo_I_Paranapanema_22-10-2026.pdf'
TITLE='ANEXO I — Resumo para o Relatório Anual / reunião em números'
REV_DATE='26/10/2026'
NAME='José Aguiar de Lima Jr.'
ROLE='Especialista em Geoprocessamento'
SITE='https://7it0.github.io/soe-salas-prototipo/paranapanema/10a-2026-10-22/'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BLUE='#215575';GREEN='#146E60'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(s):return html.escape(str(s),quote=True)
def norm(s):return re.sub(r'\s+',' ',s).strip()
def fmt(s):return s if ',' in s else f'{int(s):,}'.replace(',','.')

def annex_data(rows):
    assert len(rows)==29,'Review changed analytical base before applying this revision'
    used=set()
    def get(inst,place,var):
        found=[(i,r) for i,r in enumerate(rows) if (r['instituicao'],r['local'],r['indicador'])==(inst,place,var)]
        assert len(found)==1,(inst,place,var)
        i,r=found[0];used.add(i);return r
    specs=[('ONS','ENA','ENA — aporte energético','ENA elevada; não representa volume útil de um reservatório.'),('ONS','EAR','EAR — estoque energético','Posição agregada da bacia; não se confunde com VU individual.'),('CEMADEN','Precipitação acumulada','Chuva observada','Acumulado parcial; não representa fechamento de outubro.'),('CEMADEN','Precipitação climatológica outubro','Referência de chuva','Climatologia do mês inteiro; não é referência dos mesmos 20 dias.'),('CEMADEN','Chuva GEFS em 14 dias','Chuva GEFS — 14 dias','Valor aproximado e probabilístico; não equivale a afluência.')]
    basin=[]
    for inst,var,label,reading in specs:
        r=get(inst,'Bacia Paranapanema',var)
        value=('≈ ' if var=='Chuva GEFS em 14 dias' else '')+fmt(r['valor'])+' '+r['unidade']
        nature={'observado_parcial':'Observado parcial','observado':'Observado','referencia_climatologica':'Climatologia','previsao; valor aproximado':'Previsão'}[r['natureza']]
        basin.append([label,value,r['periodo'],nature,reading,('O' if inst=='ONS' else 'C')+', p. '+r['pagina_fonte']])
    tsi=[]
    for place in ['Rosana','Capivara','Jurumirim']:
        a=get('CEMADEN',place,'TSI-6');b=get('CEMADEN',place,'TSI-3')
        cls=lambda r:r['natureza'].split(';',1)[1].strip().capitalize()
        reading='Excesso moderado nas duas janelas.' if place!='Jurumirim' else 'Excesso na janela de 3 meses; normalidade na de 6 meses.'
        tsi.append([place,a['valor']+' — '+cls(a),b['valor']+' — '+cls(b),reading,'C, pp. 8–9'])
    observed=[];projected=[]
    for place in ['Jurumirim','Chavantes','Capivara','Mauá']:
        vu=get('ONS',place,'Volume útil IPDO')
        if place!='Mauá':
            a=get('ONS',place,'Vazão afluente');d=get('ONS',place,'Vazão defluente')
            vals=[fmt(a['valor']),fmt(d['valor'])];source='O, pp. 9 e '+a['pagina_fonte']
            reading='Defluência acima da afluência no ponto final do painel.'
            if place=='Capivara':reading='Maior magnitude de vazões do conjunto; acompanhar passagem a jusante.'
        else:
            vals=['—','—'];source='O, p. 9';reading='Estoque de 94% VU; vazões observadas não constam da base selecionada.'
        observed.append([place,vu['valor']+'%',*vals,reading,source])
        q=get('ONS',place,'Defluência média simulada');v=get('ONS',place,'Volume útil final simulado')
        reading={'Jurumirim':'Projeção de 85% VU, condicionada aos aportes e à operação simulada.','Chavantes':'Projeção de 78% VU; acompanhar aderência das afluências ao cenário.','Capivara':'Não confundir a média simulada de defluência com o valor observado de 5.062 m³/s.','Mauá':'Projeção final de 94% VU; não é garantia de estoque.'}[place]
        projected.append([place,fmt(q['valor']),v['valor']+'%',reading,'O, pp. 20–21'])
    assert used==set(range(29)),'Not all approved indicators are represented'
    return [
      {'title':'I.1 — Síntese hidroclimática e indicadores da bacia',
       'intro':'Reunião de 22/10/2026. Leitura integrada: aportes elevados e estoques relevantes, com atenção à propagação de vazões pela cascata. Síntese da análise já publicada; não constitui nova decisão operativa.',
       'tables':[{'title':'Principais números — preservando a natureza e o período de cada dado','headers':['Dimensão','Valor / unidade','Referência temporal','Natureza','Leitura analítica','Fonte'],'rows':basin,'widths':[90,90,147,82,247,90]},
                 {'title':'TSI — índice bivariado, adimensional; outubro de 2026 parcial','headers':['Recorte','TSI-6 / classe','TSI-3 / classe','Leitura entre escalas','Fonte'],'rows':tsi,'widths':[90,170,170,226,90]}],
       'notes':['<b>Comparabilidade:</b> 122,0 mm até 20/10 e 135,5 mm da climatologia mensal têm durações distintas. Não se calcula um desvio para períodos iguais a partir desses dois valores.',
                '<b>Interpretação:</b> as classes do TSI são as informadas pelo CEMADEN. Índice de excesso não mede volume armazenado nem comprova inundação; previsão de chuva não é observação.']},
      {'title':'I.2 — Reservatórios, operação e cenários',
       'intro':'Observações e projeções estão em quadros separados. VU = volume útil; vazões em m³/s. Os traços indicam ausência na base selecionada, e não valor zero.',
       'tables':[{'title':'Condições observadas — VU em 21/10; vazões destacadas nos painéis até 20/10','headers':['Reservatório','VU em 21/10','Afluência\n(m³/s)','Defluência\n(m³/s)','Leitura operacional','Fonte'],'rows':observed,'widths':[100,88,88,88,292,90]},
                 {'title':'Cenário ONS de 22/10 a 30/11 — SMAP/ONS com chuva ECMWF','headers':['Reservatório','Defluência média\nsimulada (m³/s)','VU final projetado\naté 30/11','Leitura / limite do cenário','Fonte'],'rows':projected,'widths':[100,142,136,278,90]}],
       'notes':['<b>Cortes diferentes:</b> o VU observado em 21/10 não é automaticamente a condição inicial da simulação de 22/10. Não se apresenta a diferença entre colunas como variação observada.',
                '<b>Subsídio ao Conjuntura:</b> consolidar apenas observações comparáveis, preservando data, unidade e fonte. Não somar percentuais de VU ou ENA, misturar previsões na série observada nem tratar esta síntese como estatística anual homologada.',
                '<b>Memória técnica:</b> os 29 registros da base tabular foram mantidos. A análise, as reproduções e as ressalvas operacionais/regulatórias permanecem na NT; nenhuma nova decisão foi atribuída à reunião.']}
    ]

def fonts():
    pdfmetrics.registerFont(TTFont('NT',FONT));pdfmetrics.registerFont(TTFont('NTB',BOLD))
    pdfmetrics.registerFontFamily('NT',normal='NT',bold='NTB',italic='NT',boldItalic='NTB')
def styles():
    return {'title':ParagraphStyle('title',fontName='NTB',fontSize=13.4,leading=17,textColor=colors.HexColor(BLUE),spaceAfter=6),
    'sub':ParagraphStyle('sub',fontName='NTB',fontSize=10.4,leading=13.4,textColor=colors.HexColor(GREEN),spaceBefore=8,spaceAfter=6),
    'body':ParagraphStyle('body',fontName='NT',fontSize=8.8,leading=11.5,spaceAfter=6),
    'head':ParagraphStyle('head',fontName='NTB',fontSize=8.3,leading=10.5,textColor=colors.white),
    'cell':ParagraphStyle('cell',fontName='NT',fontSize=8.6,leading=11),
    'note':ParagraphStyle('note',fontName='NT',fontSize=8,leading=10.5,spaceAfter=4)}
def furniture(c,doc):
    w,h=doc.pagesize;c.saveState();c.setFillColor(colors.HexColor('#4A6976'));c.setStrokeColor(colors.HexColor('#BDD1DC'));c.setFont('NT',7)
    c.drawString(48,h-23,'SOE/ANA — GABINETE | Paranapanema — 10ª reunião — 22/10/2026 | Revisão 1.1 — '+REV_DATE)
    c.line(48,h-30,w-48,h-30);c.line(48,47,w-48,47)
    c.drawCentredString(w/2,35,f'Supervisionado por {NAME} · {ROLE}')
    c.drawCentredString(w/2,24,'Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)')
    c.drawRightString(w-48,13,f'Anexo I · {doc.page} / 2');c.restoreState()
def annex_pdf(out,blocks):
    st=styles();story=[]
    for i,b in enumerate(blocks):
        if i:story.append(PageBreak())
        story += [Paragraph(TITLE,st['title']),Paragraph(b['title'],st['sub']),Paragraph(esc(b['intro']),st['body'])]
        for t in b['tables']:
            story.append(Paragraph(esc(t['title']),st['sub']))
            cells=[[Paragraph(esc(v).replace('\n','<br/>'),st['head']) for v in t['headers']]]
            cells += [[Paragraph(esc(v),st['cell']) for v in row] for row in t['rows']]
            tb=Table(cells,colWidths=t['widths'],repeatRows=1,hAlign='LEFT')
            tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(BLUE)),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#C5D7DE')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F6F7')]),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story.append(tb)
        story.append(Spacer(1,8));story += [Paragraph(v,st['note']) for v in b['notes']]
        story.append(Paragraph(f'Fontes: <link href="{SITE}fontes/cemaden.pdf">C = CEMADEN</link>; <link href="{SITE}fontes/ons.pdf">O = ONS</link>. Apresentações de 22/10/2026; páginas físicas dos PDFs. MLT = média de longo termo; EAR = energia armazenada; ENA = energia natural afluente.',st['note']))
    path=out/'documentos'/ANNEX
    SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=48,rightMargin=48,topMargin=40,bottomMargin=54,title=TITLE,author=f'{NAME} — {ROLE} — SOE/ANA').build(story,onFirstPage=furniture,onLaterPages=furniture)
    with fitz.open(path) as d:assert len(d)==2,f'Annex pagination: {len(d)} pages'
    return path

def put(page,rect,text,size=8,bold=False,align=0):
    font=BOLD if bold else FONT;name='AnxBold' if bold else 'Anx';page.insert_font(fontname=name,fontfile=font)
    n=page.insert_textbox(rect,text,fontname=name,fontfile=font,fontsize=size,align=align,color=(.13,.33,.46))
    assert n>=0,(text,n)
def erase(page,rect):
    page.add_redact_annot(rect,fill=(1,1,1));page.apply_redactions(images=0,graphics=0)
def combine_pdf(base,out,annex,soup):
    src=base/'documentos'/PDF;old=fitz.open(src);assert len(old)==35
    entries=[]
    for sec in soup.select('main section.chapter'):
        title=sec.h2.get_text(' ',strip=True)
        matches=[i for i in range(2,len(old)) if norm(title) in norm(old[i].get_text())]
        assert matches,title;entries.append([1,title,matches[0]+1])
    entries.append([1,'ANEXO I — Resumo anual / reunião em números',36])
    doc=fitz.open(src)
    with fitz.open(annex) as a:doc.insert_pdf(a)
    assert len(doc)==37
    for i in range(35):
        p=doc[i];found=p.search_for(f'Reunião 22/10/2026 · Edição 23/10/2026 · Página {i+1} de 35')
        assert len(found)==1,(i,found);erase(p,found[0]+(-2,-1,2,1))
        put(p,fitz.Rect(45,817,p.rect.width-45,832),f'Reunião 22/10/2026 · Revisão 1.1 — {REV_DATE} · Página {i+1} de 37',6,align=1)
    for i in range(2):
        p=doc[35+i];found=p.search_for(f'Anexo I · {i+1} / 2');assert len(found)==1
        erase(p,found[0]+(-1,-1,2,1));put(p,fitz.Rect(p.rect.width-210,p.rect.height-22,p.rect.width-48,p.rect.height-6),f'Anexo I · Página {36+i} de 37',7,align=2)
    p=doc[0];found=p.search_for('CEMADEN + ONS · 24 figuras originais · Edição 1.0');assert len(found)==1
    r=found[0];erase(p,r+(-1,-1,2,1));put(p,fitz.Rect(r.x0,r.y0-1,p.rect.width-45,r.y0+22),'CEMADEN + ONS · 24 figuras originais · Revisão 1.1',9)
    put(p,fitz.Rect(45,520,p.rect.width-45,574),'Revisão editorial 1.1 — 26/10/2026: inclusão do Anexo I (páginas 36–37)\ne do sumário paginado. Análise, figuras e base tabular preservadas.',9)
    st=styles();buff=io.BytesIO();story=[Paragraph('SUMÁRIO',st['title'])]
    for ptag in soup.select_one('.contents').find_all('p',recursive=False):story.append(Paragraph(esc(ptag.get_text(' ',strip=True)),st['body']))
    story.append(Spacer(1,10))
    for _,title,page in entries:
        t=Table([[Paragraph(esc(title),st['body']),Paragraph(str(page),st['body'])]],colWidths=[466,32]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D8E3E7'))]));story.append(t)
    story += [Spacer(1,12),Paragraph('Revisão 1.1: Anexo I com os 29 indicadores organizados para consulta rápida e subsídio ao Relatório Anual / Conjuntura. A base CSV permanece inalterada.',st['body'])]
    SimpleDocTemplate(buff,pagesize=(doc[1].rect.width,doc[1].rect.height),leftMargin=45,rightMargin=45,topMargin=52,bottomMargin=66).build(story)
    toc=fitz.open(stream=buff.getvalue(),filetype='pdf');assert len(toc)==1
    p=doc[1]
    for link in p.get_links():p.delete_link(link)
    erase(p,fitz.Rect(0,0,p.rect.width,790));p.show_pdf_page(p.rect,toc,0)
    for _,title,page in entries:
        found=p.search_for(title)
        if found:
            r=found[0]
            for r2 in found[1:]:r|=r2
            p.insert_link({'kind':fitz.LINK_GOTO,'from':r,'page':page-1})
    toc.close();doc.set_toc(entries)
    p=doc[34];r=p.search_for('Versão 1.0.');assert len(r)==1
    erase(p,r[0]+(-.5,-.4,.5,.4));put(p,fitz.Rect(r[0].x0,r[0].y0-.5,r[0].x1+3,r[0].y1+4),'Versão 1.1.',8.4)
    meta=doc.metadata;meta.update({'title':'NT Paranapanema — 10ª reunião — 22/10/2026 — revisão 1.1','subject':'Inclusão do Anexo I numérico — revisão editorial de 26/10/2026; conteúdo técnico preservado'})
    doc.set_metadata(meta);path=out/'documentos'/PDF;doc.save(path,garbage=3,deflate=True);doc.close()
    revised=fitz.open(path)
    for i in range(35):
        clip=fitz.Rect(0,0,old[i].rect.width,790)
        if i not in (0,1,34):
            assert old[i].get_text(clip=clip)==revised[i].get_text(clip=clip),f'Text changed on page {i+1}'
            assert old[i].get_pixmap(matrix=fitz.Matrix(.6,.6),clip=clip,alpha=False).samples==revised[i].get_pixmap(matrix=fitz.Matrix(.6,.6),clip=clip,alpha=False).samples,f'Visual body changed on page {i+1}'
        a=[(x['bbox'],x['digest']) for x in old[i].get_image_info(hashes=True)]
        b=[(x['bbox'],x['digest']) for x in revised[i].get_image_info(hashes=True)]
        assert a==b,f'Image changed on page {i+1}'
    for i,p in enumerate(revised):
        assert f'Página {i+1} de 37' in p.get_text(),i
        assert NAME in p.get_text() and ROLE in p.get_text() and 'inteligência artificial' in p.get_text()
    assert len(revised.get_toc())==11
    old.close();revised.close();return entries

def annex_html(blocks):
    parts=[f'<section class="chapter" id="anexo-i"><div class="tag">Síntese numérica · revisão 1.1</div><h2>{esc(TITLE)}</h2><p>Consulta rápida às principais variáveis e à sua leitura analítica. Os 29 registros da base tabular estão representados abaixo, sem substituir a análise integral ou a base para BI.</p>']
    for b in blocks:
        parts += [f'<h3>{esc(b["title"])}</h3>',f'<p>{esc(b["intro"])}</p>']
        for t in b['tables']:
            heads=''.join('<th scope="col">'+esc(v).replace('\n','<br>')+'</th>' for v in t['headers'])
            cells=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in t['rows'])
            parts.append('<h4>'+esc(t['title'])+'</h4><div class="tablewrap"><table><thead><tr>'+heads+'</tr></thead><tbody>'+cells+'</tbody></table></div>')
        parts += ['<p class="small">'+n+'</p>' for n in b['notes']]
    parts += [f'<p class="small">Fontes: <a href="fontes/cemaden.pdf">C = CEMADEN</a>; <a href="fontes/ons.pdf">O = ONS</a>. Apresentações de 22/10/2026; páginas físicas dos PDFs. MLT: média de longo termo; EAR: energia armazenada; ENA: energia natural afluente.</p>',f'<p><a href="documentos/{ANNEX}" download>Baixar somente o Anexo I — PDF de 2 páginas</a> · <a href="indicadores.csv" download>Dados e indicadores — CSV preservado</a></p></section>']
    return ''.join(parts)
def edit_html(soup,out,blocks):
    before={sec['id']:str(sec) for sec in soup.select('main section.chapter')}
    imgs=[str(x) for x in soup.select('figure')];credits=[str(x) for x in soup.select('.credit')]
    assert soup.find(id='anexo-i') is None
    soup.main.append(BeautifulSoup(annex_html(blocks),'html.parser').section)
    data=soup.select_one('header .actions a[href="indicadores.csv"]');assert data
    group=soup.new_tag('div',attrs={'class':'nt-data-actions','role':'group','aria-label':'Dados analíticos e síntese numérica'})
    data.insert_before(group);group.append(data.extract())
    a=soup.new_tag('a',href='#anexo-i');a.string='Anexo I — Reunião em números';group.append(a)
    style=soup.new_tag('style',id='anexo-i-style');style.string='.actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.nt-data-actions{grid-column:1/-1;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.actions a{min-width:0}.contents .toc-list{columns:2;list-style:none;padding-left:0}.toc-list li{margin:8px 0;break-inside:avoid}@media(max-width:820px){.actions,.nt-data-actions{grid-template-columns:1fr}.contents .toc-list{columns:1}}@media print{header .actions{display:none!important}}';soup.head.append(style)
    ol=soup.select_one('.contents ol');ul=soup.new_tag('ul',attrs={'class':'toc-list'})
    for sec in soup.select('main section.chapter'):
        li=soup.new_tag('li');a=soup.new_tag('a',href='#'+sec['id']);a.string=sec.h2.get_text();li.append(a);ul.append(li)
    ol.replace_with(ul)
    a=soup.new_tag('a',href='#anexo-i');a.string='Reunião em números';soup.nav.append(a)
    for node in list(soup.header.find_all(string=True)):
        if 'Edição 1.0' in node:node.replace_with(node.replace('Edição 1.0','Revisão 1.1 · Anexo I incluído'))
    for node in list(soup.footer.find_all(string=True)):
        if 'Versão 1.0' in node:node.replace_with(node.replace('Versão 1.0','Versão 1.1'))
    p=soup.new_tag('p',attrs={'class':'small'});p.string='Revisão editorial 1.1 — 26/10/2026: inclusão do Anexo I nas páginas 36–37 do PDF integral e sumário paginado. As 24 figuras, a análise e o CSV de 29 registros foram preservados.';soup.footer.append(p)
    for key,original in before.items():assert str(soup.find(id=key))==original,key
    assert [str(x) for x in soup.select('figure')]==imgs
    assert [str(x) for x in soup.select('.credit')]==credits
    (out/'index.html').write_text(str(soup),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();base=a.base.resolve();out=a.output.resolve();assert base!=out
    out.mkdir(parents=True,exist_ok=True);(out/'documentos').mkdir(exist_ok=True)
    m=json.loads((base/'manifesto.json').read_text(encoding='utf-8'));assert m['version']=='1.0','Apply only to edition 1.0; reconcile later revisions'
    assert sha(base/'documentos'/PDF)==m['pdf_sha256']
    csv_hash=sha(base/'indicadores.csv');rows=list(csv.DictReader((base/'indicadores.csv').open(encoding='utf-8-sig',newline=''),delimiter=';'))
    fonts();blocks=annex_data(rows);annex=annex_pdf(out,blocks)
    soup=BeautifulSoup((base/'index.html').read_text(encoding='utf-8'),'html.parser')
    toc=combine_pdf(base,out,annex,soup);edit_html(soup,out,blocks)
    shutil.copyfile(base/'indicadores.csv',out/'indicadores.csv');assert sha(out/'indicadores.csv')==csv_hash
    old_hash=m['pdf_sha256'];m.update({'version':'1.1','revision_date':'2026-10-26','pdf_pages':37,'pdf_sha256':sha(out/'documentos'/PDF)})
    m['anexo_i']={'title':TITLE,'anchor':'anexo-i','pdf':'documentos/'+ANNEX,'pdf_pages':2,'full_pdf_pages':[36,37],'records':29,'button_after':'Dados e indicadores','sha256':sha(annex)}
    m['editorial_revision']={'description':'Anexo I analítico e resumido, com sumário paginado e botão adjacente aos dados','previous_pdf_sha256':old_hash,'csv_sha256':csv_hash,'csv_unchanged':True,'original_analysis_preserved':True,'original_24_figures_preserved':True,'toc_entries':len(toc),'observed_and_projected_separated':True}
    (out/'manifesto.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'ANEXO_I.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'REVISAO_1_1.md').write_text('# Paranapanema — revisão editorial 1.1\n\nReunião: 22/10/2026. Revisão: 26/10/2026.\n\nAnexo I nas páginas 36–37 da NT integral de 37 páginas, também disponível como PDF independente de 2 páginas e no HTML, ao lado de Dados e indicadores.\n\nOs 29 registros do CSV, as 24 figuras e os capítulos técnicos originais foram preservados. Incluído sumário paginado e corrigida sua numeração duplicada. Observações, climatologia e projeções permanecem distintas.\n\nO gerador da edição 1.0 não deve substituir esta publicação sem reaplicar o Anexo I e suas verificações.\n',encoding='utf-8')
    print('VERIFIED: 2-page annex; 37-page integral PDF; 29 indicators; 24 figures and analytical body preserved; identical CSV.',flush=True)
if __name__=='__main__':main()
