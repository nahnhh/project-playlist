```dataviewjs
const {createYamlProperty} = this.app.plugins.plugins["metaedit"].api
const {createButton} = app.plugins.plugins["buttons"]

let mainTag = `lol`

		let pages = dv.pages(mainTag)

dv.header(3, mainTag);
dv.table(["X", "C", "B", "T", "Name"], pages
	.sort(b => b.canva, 'desc')
	.sort(b => b.file.etags.length, 'asc')
	.sort(b => b.beat, 'asc')
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