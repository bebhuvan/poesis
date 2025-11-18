# How to Use Your Blog

Welcome! You now have a beautiful blog set up and ready to use. **No coding required!**

## Quick Start - See Your Blog

To see your blog in action:

1. Open your terminal
2. Navigate to your blog folder:
   ```bash
   cd /home/user/poesis/blog
   ```
3. Start the blog server:
   ```bash
   hugo server
   ```
4. Open your web browser and go to: `http://localhost:1313`

You should see your blog! Press `Ctrl+C` in the terminal to stop the server.

---

## How to Write a New Blog Post

Writing a blog post is simple - just create a text file! Here's how:

### Method 1: Using Hugo Command (Recommended)

1. Open your terminal
2. Go to your blog folder:
   ```bash
   cd /home/user/poesis/blog
   ```
3. Create a new post:
   ```bash
   hugo new posts/my-post-title.md
   ```
4. Find your new post in `content/posts/my-post-title.md`
5. Open it with any text editor and start writing!

### Method 2: Create the File Manually

1. Create a new file in `content/posts/` folder
2. Name it something like `my-awesome-post.md`
3. Add this at the top:
   ```
   ---
   title: "My Awesome Post"
   date: 2025-11-18
   draft: false
   tags: ["personal", "life"]
   ---
   ```
4. Write your content below!

---

## Writing Your Post Content

You can write using simple formatting:

### Headings
```
# Big Heading
## Medium Heading
### Small Heading
```

### Text Formatting
```
**Bold text**
*Italic text*
```

### Lists
```
- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third
```

### Links
```
[Click here](https://example.com)
```

### Images
```
![Image description](image.jpg)
```

---

## Customize Your Blog

### Change Blog Title and Description

1. Open `hugo.toml` file
2. Change these lines:
   ```
   title = 'My Blog'  ← Change this to your blog name
   ```
3. Under `[params]`:
   ```
   description = "Welcome to my blog"  ← Change this
   author = "Your Name"  ← Add your name
   ```

### Change Homepage Welcome Message

1. Open `hugo.toml` file
2. Find `[params.homeInfoParams]`
3. Change:
   ```
   Title = "Welcome to My Blog"  ← Your welcome title
   Content = "This is my personal blog..."  ← Your welcome message
   ```

---

## Publishing Your Blog Online

When you're ready to share your blog with the world, you have several free options:

### Option 1: GitHub Pages (Recommended for Beginners)

1. Create a free account on [GitHub](https://github.com)
2. Create a new repository called `yourusername.github.io`
3. Build your blog:
   ```bash
   cd /home/user/poesis/blog
   hugo
   ```
4. Upload the `public/` folder to your GitHub repository
5. Your blog will be live at `https://yourusername.github.io`

### Option 2: Netlify (Easiest)

1. Create a free account on [Netlify](https://netlify.com)
2. Drag and drop your `public/` folder after running `hugo`
3. Your blog is live instantly!

### Option 3: Vercel

1. Create a free account on [Vercel](https://vercel.com)
2. Connect your Git repository
3. Vercel will automatically build and deploy your blog

---

## Tips for Blogging

1. **Write regularly** - Even short posts are great!
2. **Be yourself** - Your unique voice is what makes your blog special
3. **Use tags** - They help organize your posts
4. **Save drafts** - Set `draft: true` for posts you're not ready to publish
5. **Preview before publishing** - Always check `http://localhost:1313` first

---

## Common Tasks

### See your blog locally
```bash
cd /home/user/poesis/blog
hugo server
```
Then visit: `http://localhost:1313`

### Create a new post
```bash
cd /home/user/poesis/blog
hugo new posts/my-new-post.md
```

### Build your blog for publishing
```bash
cd /home/user/poesis/blog
hugo
```
This creates a `public/` folder with your complete website

---

## Getting Help

- Example posts are in `content/posts/` - look at them for inspiration
- The PaperMod theme documentation: https://github.com/adityatelange/hugo-PaperMod
- Hugo documentation: https://gohugo.io/documentation/

---

## File Structure

```
blog/
├── content/          ← Your blog posts go here!
│   ├── posts/       ← Create new posts in this folder
│   └── about.md     ← Your about page
├── hugo.toml        ← Main settings file
├── themes/          ← The theme (don't change this)
└── public/          ← Generated website (created when you run 'hugo')
```

---

## Remember

- You don't need to know coding!
- Just create `.md` files and write in plain text
- The blog will automatically look beautiful
- Preview changes before publishing
- Have fun writing!

**Happy blogging!** 🎉
