### Search:: irst
```dataviewjs
let searchKey = dv.page("Search Engine")["Search"]

const {createYamlProperty} = this.app.plugins.plugins["metaedit"].api
const {createButton} = app.plugins.plugins["buttons"]

dv.table(["X", "Canva", "Beat", "Tags", "Name"],
	dv.pages()
	.where(p => p.file.name.includes(searchKey))
	.sort(b => b.file.link, 'asc')
	.map(b => [
				createButton({
					app, 
					el: this.container, 
					args: {name: "❎"}, 
					clickOverride: 
					{click: createYamlProperty, params: 
					['canva','x', b.file.path]}
							}),
				b.canva, b.beat, b.file.etags.length, b.file.link
				]
		)
	)
```