function syncBlogger() {
  const base = 'https://raw.githubusercontent.com/jwbing2016-stack/mpo-polarity-docpage-test/platform-sync-test/';
  const source = UrlFetchApp.fetch(base + 'article.md').getContentText();
  if (!source.startsWith('# ')) throw new Error('Missing Markdown title');
  const title = source.split(String.fromCharCode(10))[0].slice(2);
  const content = UrlFetchApp.fetch(base + 'article.html').getContentText();
  if (!content.includes('https://cablefam.com/')) throw new Error('Official link missing');
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('BLOGGER_TEST_POST_ID');
  const url = 'https://www.googleapis.com/blogger/v3/blogs/6555719913176040199/posts' + (id ? '/' + id : '');
  const response = UrlFetchApp.fetch(url, {
    method: id ? 'put' : 'post', contentType: 'application/json',
    headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()},
    payload: JSON.stringify({kind: 'blogger#post', title: title, content: content}),
    muteHttpExceptions: true
  });
  if (response.getResponseCode() >= 300) throw new Error('Blogger HTTP ' + response.getResponseCode() + ': ' + response.getContentText());
  const post = JSON.parse(response.getContentText());
  props.setProperty('BLOGGER_TEST_POST_ID', String(post.id));
  props.setProperty('BLOGGER_TEST_POST_URL', post.url);
  console.log('Published or updated: ' + post.url);
}
