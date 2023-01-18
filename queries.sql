/*Creation table in database.*/
CREATE TABLE articles (
    article_name varchar(255),
    links_name varchar(20000),
    links_count int,
    links_in_article int,
    descendants int 
);

/*Top 5 most popular articles*/
SELECT article_name, links_count FROM articles
ORDER BY - links_count 
limit 5

/*Top 5 articles with the most links to other articles*/
SELECT article_name, links_in_article FROM articles
ORDER BY - links_in_article 
limit 5

/*The average number of descendants of the second level*/
SELECT AVG(descendants) AS Averege FROM articles;
