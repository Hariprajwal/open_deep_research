// IEEE Conference / Journal Typst Template

#let ieee(
  title: [Research Title],
  authors: (),
  abstract: [],
  keywords: (),
  body
) = {
  set page(
    paper: "us-letter",
    margin: (x: 0.625in, top: 0.75in, bottom: 1.0in),
  )
  
  set text(
    font: "Times New Roman",
    size: 10pt,
    lang: "en"
  )
  
  set par(justify: true, leading: 0.55em)
  
  // Title
  align(center)[
    #text(size: 24pt, weight: "bold")[#title]
    #v(1em)
    #if authors.len() > 0 [
      #grid(
        columns: (1fr,) * calc.min(authors.len(), 3),
        gutter: 1.5em,
        ..authors.map(a => [
          #text(size: 11pt, weight: "bold")[#a.name] \
          #text(size: 9pt)[#a.affiliation] \
          #text(size: 9pt, style: "italic")[#a.email]
        ])
      )
    ]
    #v(1.5em)
  ]
  
  // Abstract & Keywords
  if abstract != [] [
    #rect(width: 100%, stroke: none, fill: rgb("f8f9fa"), inset: 10pt)[
      #text(weight: "bold")[Abstract—] #abstract
      #if keywords.len() > 0 [
        \ \
        #text(weight: "bold", style: "italic")[Keywords—] #keywords.join(", ")
      ]
    ]
    #v(1em)
  ]
  
  // Two Column Body Layout
  show heading: it => [
    #v(0.8em)
    #if it.level == 1 [
      #align(center)[#text(size: 10pt, weight: "bold")[#upper(it.body)]]
    ] else if it.level == 2 [
      #text(size: 10pt, weight: "bold", style: "italic")[#it.body]
    ] else [
      #text(size: 10pt, style: "italic")[#it.body]
    ]
    #v(0.4em)
  ]
  
  columns(2, gutter: 0.25in, body)
}
