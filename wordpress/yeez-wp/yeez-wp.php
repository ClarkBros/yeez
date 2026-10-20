<?php
/**
 * Plugin Name:       Yeez for WordPress
 * Plugin URI:        https://clarkbrosmedia.com/yeez/
 * Description:       Connects your site to Yeez for search: sets each article's SEO title, description and focus topic in your SEO plugin (Yoast, Rank Math or SEOPress), marks articles as news articles for Google, keeps a Google News sitemap, tells Bing about new posts (IndexNow), keeps tag pages out of search, and reports your site's search setup to Yeez.
 * Version:           1.0.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Clark Bros Media
 * Author URI:        https://clarkbrosmedia.com/
 * License:           GPL-2.0-or-later
 * Text Domain:       yeez-wp
 */

if (!defined('ABSPATH')) exit;
define('YEEZ_WP_VERSION', '1.0.0');

/* ------------------------------------------------------------------ which SEO plugin is active */

function yeez_wp_seo_plugin() {
    if (defined('WPSEO_VERSION')) return 'yoast';
    if (defined('RANK_MATH_VERSION')) return 'rankmath';
    if (defined('SEOPRESS_VERSION')) return 'seopress';
    return 'none';
}

/* ------------------------------------------------------------------ 1. SEO fields Yeez can set */

add_action('init', function () {
    register_post_meta('post', '_yeez_seo', array(
        'type'          => 'object',
        'single'        => true,
        'show_in_rest'  => array('schema' => array(
            'type'                 => 'object',
            'additionalProperties' => false,
            'properties'           => array(
                'title'       => array('type' => 'string'),
                'description' => array('type' => 'string'),
                'focus'       => array('type' => 'string'),
                'news'        => array('type' => 'boolean'),
                'search'      => array('type' => 'boolean'),
            ),
        )),
        'auth_callback' => function () { return current_user_can('edit_posts'); },
    ));
});

/** Copy Yeez's SEO fields into whichever SEO plugin the site uses. */
function yeez_wp_sync_seo($post_id) {
    $s = get_post_meta($post_id, '_yeez_seo', true);
    if (!is_array($s)) return;
    $t = isset($s['title']) ? sanitize_text_field($s['title']) : '';
    $d = isset($s['description']) ? sanitize_text_field($s['description']) : '';
    $f = isset($s['focus']) ? sanitize_text_field($s['focus']) : '';
    $map = array(
        'yoast'    => array('_yoast_wpseo_title', '_yoast_wpseo_metadesc', '_yoast_wpseo_focuskw'),
        'rankmath' => array('rank_math_title', 'rank_math_description', 'rank_math_focus_keyword'),
        'seopress' => array('_seopress_titles_title', '_seopress_titles_desc', '_seopress_analysis_target_kw'),
    );
    $p = yeez_wp_seo_plugin();
    if (!isset($map[$p])) return;
    list($kt, $kd, $kf) = $map[$p];
    if ($t !== '') update_post_meta($post_id, $kt, $t);
    if ($d !== '') update_post_meta($post_id, $kd, $d);
    if ($f !== '') update_post_meta($post_id, $kf, $f);
}
add_action('rest_after_insert_post', function ($post) { yeez_wp_sync_seo($post->ID); }, 20);
add_action('updated_post_meta', function ($mid, $post_id, $key) { if ($key === '_yeez_seo') yeez_wp_sync_seo($post_id); }, 10, 3);
add_action('added_post_meta', function ($mid, $post_id, $key) { if ($key === '_yeez_seo') yeez_wp_sync_seo($post_id); }, 10, 3);

/* ------------------------------------------------------------------ 2. title, description and schema */

function yeez_wp_seo_for($post_id) {
    $s = get_post_meta($post_id, '_yeez_seo', true);
    return is_array($s) ? $s : array();
}

/* Sites with no SEO plugin: Yeez prints the title, description, social image tags and the schema itself. */
add_filter('pre_get_document_title', function ($title) {
    if (yeez_wp_seo_plugin() !== 'none' || !is_singular('post')) return $title;
    $s = yeez_wp_seo_for(get_queried_object_id());
    return !empty($s['title']) ? $s['title'] . ' - ' . get_bloginfo('name') : $title;
}, 20);

add_action('wp_head', function () {
    if (!is_singular('post')) return;
    $id = get_queried_object_id();
    $s = yeez_wp_seo_for($id);
    $plugin = yeez_wp_seo_plugin();
    if ($plugin === 'none') {
        $desc = !empty($s['description']) ? $s['description'] : wp_strip_all_tags(get_the_excerpt($id));
        $img = get_the_post_thumbnail_url($id, 'full');
        echo '<meta name="description" content="' . esc_attr($desc) . "\">\n";
        echo '<meta property="og:type" content="article">' . "\n";
        echo '<meta property="og:title" content="' . esc_attr(!empty($s['title']) ? $s['title'] : get_the_title($id)) . "\">\n";
        echo '<meta property="og:description" content="' . esc_attr($desc) . "\">\n";
        echo '<meta property="og:url" content="' . esc_url(get_permalink($id)) . "\">\n";
        if ($img) echo '<meta property="og:image" content="' . esc_url($img) . "\">\n" . '<meta name="twitter:card" content="summary_large_image">' . "\n";
    }
    if ($plugin === 'none' || $plugin === 'seopress') {
        echo '<script type="application/ld+json">' . wp_json_encode(yeez_wp_article_schema($id)) . "</script>\n";
    }
}, 5);

function yeez_wp_article_schema($id) {
    $post = get_post($id);
    $author_id = (int) $post->post_author;
    $img_id = get_post_thumbnail_id($id);
    $imgs = array();
    if ($img_id) {
        foreach (array('full', 'large') as $size) { $u = wp_get_attachment_image_url($img_id, $size); if ($u && !in_array($u, $imgs, true)) $imgs[] = $u; }
    }
    $logo = get_site_icon_url(512);
    $data = array(
        '@context'         => 'https://schema.org',
        '@type'            => 'NewsArticle',
        'headline'         => wp_strip_all_tags(get_the_title($id)),
        'datePublished'    => get_the_date('c', $id),
        'dateModified'     => get_the_modified_date('c', $id),
        'mainEntityOfPage' => get_permalink($id),
        'author'           => array(array('@type' => 'Person', 'name' => get_the_author_meta('display_name', $author_id), 'url' => get_author_posts_url($author_id))),
        'publisher'        => array_filter(array('@type' => 'Organization', 'name' => get_bloginfo('name'), 'url' => home_url('/'), 'logo' => $logo ? array('@type' => 'ImageObject', 'url' => $logo) : null)),
    );
    if ($imgs) $data['image'] = $imgs;
    $s = yeez_wp_seo_for($id);
    if (!empty($s['description'])) $data['description'] = $s['description'];
    return $data;
}

/* Yoast and Rank Math already print Article schema: make Yeez's posts NewsArticle there. */
add_filter('wpseo_schema_article_type', function ($type) {
    $s = is_singular('post') ? yeez_wp_seo_for(get_queried_object_id()) : array();
    if (empty($s['news'])) return $type;
    $t = (array) $type;
    if (!in_array('NewsArticle', $t, true)) $t[] = 'NewsArticle';
    return $t;
});
add_filter('rank_math/snippet/rich_snippet_article_entity', function ($entity) {
    $s = is_singular('post') ? yeez_wp_seo_for(get_queried_object_id()) : array();
    if (!empty($s['news'])) $entity['@type'] = 'NewsArticle';
    return $entity;
});

/* ------------------------------------------------------------------ 3. robots: big image previews, tag pages out of search */

add_filter('wp_robots', function ($robots) {
    if (get_option('blog_public')) $robots['max-image-preview'] = 'large';
    if (get_option('yeez_wp_noindex_tags', '1') === '1' && is_tag()) { $robots['noindex'] = true; $robots['follow'] = true; }
    return $robots;
});

add_filter('robots_txt', function ($out, $public) {
    if (!$public) return $out;
    $lines = array('Sitemap: ' . home_url('/yeez-news-sitemap.xml'));
    if (stripos($out, 'sitemap:') === false) {
        $main = yeez_wp_main_sitemap();
        if ($main) $lines[] = 'Sitemap: ' . $main;
    }
    return rtrim($out) . "\n" . implode("\n", $lines) . "\n";
}, 20, 2);

function yeez_wp_main_sitemap() {
    $p = yeez_wp_seo_plugin();
    if ($p === 'yoast' || $p === 'rankmath') return home_url('/sitemap_index.xml');
    if ($p === 'seopress') return home_url('/sitemaps.xml');
    return function_exists('wp_sitemaps_get_server') ? home_url('/wp-sitemap.xml') : '';
}

/* ------------------------------------------------------------------ 4. Google News sitemap + IndexNow key file */

add_action('init', function () {
    $path = isset($_SERVER['REQUEST_URI']) ? wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']), PHP_URL_PATH) : '';
    $home = wp_parse_url(home_url('/'), PHP_URL_PATH) ?: '/';
    $rel = '/' . ltrim(substr($path, strlen(rtrim($home, '/'))), '/');
    if ($rel === '/yeez-news-sitemap.xml') { yeez_wp_news_sitemap(); exit; }
    $key = get_option('yeez_wp_indexnow_key');
    if ($key && $rel === '/' . $key . '.txt') { header('Content-Type: text/plain; charset=utf-8'); echo esc_html($key); exit; }
}, 1);

function yeez_wp_news_sitemap() {
    $q = new WP_Query(array('post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => 1000, 'no_found_rows' => true,
        'date_query' => array(array('after' => gmdate('Y-m-d H:i:s', time() - 2 * DAY_IN_SECONDS), 'column' => 'post_date_gmt'))));
    $name = get_bloginfo('name');
    $lang = substr(get_locale(), 0, 2);
    header('Content-Type: application/xml; charset=utf-8');
    header('X-Robots-Tag: noindex');
    echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
    echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">' . "\n";
    foreach ($q->posts as $p) {
        echo "<url><loc>" . esc_url(get_permalink($p)) . "</loc><news:news><news:publication><news:name>" . esc_html($name) . "</news:name><news:language>" . esc_html($lang) .
             "</news:language></news:publication><news:publication_date>" . esc_html(get_post_time('c', true, $p)) . "</news:publication_date><news:title>" .
             esc_html(wp_strip_all_tags(get_the_title($p))) . "</news:title></news:news></url>\n";
    }
    echo '</urlset>';
}

/* IndexNow (Bing, Yandex and others; Google doesn't use it): ping when a post goes live or changes. */
function yeez_wp_indexnow($post_id) {
    $key = get_option('yeez_wp_indexnow_key');
    if (!$key || !get_option('blog_public')) return;
    $url = get_permalink($post_id);
    wp_remote_post('https://api.indexnow.org/indexnow', array('blocking' => false, 'timeout' => 5, 'headers' => array('Content-Type' => 'application/json; charset=utf-8'),
        'body' => wp_json_encode(array('host' => wp_parse_url(home_url(), PHP_URL_HOST), 'key' => $key, 'keyLocation' => home_url('/' . $key . '.txt'), 'urlList' => array($url)))));
}
add_action('transition_post_status', function ($new, $old, $post) {
    if ($post->post_type === 'post' && $new === 'publish') yeez_wp_indexnow($post->ID);
}, 10, 3);

register_activation_hook(__FILE__, function () {
    if (!get_option('yeez_wp_indexnow_key')) update_option('yeez_wp_indexnow_key', wp_generate_password(32, false, false));
    add_option('yeez_wp_noindex_tags', '1');
});
add_action('admin_init', function () { if (!get_option('yeez_wp_indexnow_key')) update_option('yeez_wp_indexnow_key', wp_generate_password(32, false, false)); });

/* ------------------------------------------------------------------ 5. status for Yeez's setup check */

add_action('rest_api_init', function () {
    register_rest_route('yeez/v1', '/status', array(
        'methods'             => 'GET',
        'permission_callback' => function () { return current_user_can('edit_posts'); },
        'callback'            => 'yeez_wp_status',
    ));
});

function yeez_wp_status() {
    $robots = '';
    ob_start(); do_action('do_robots'); $robots = ob_get_clean();
    $blocked = array();
    foreach (array('Googlebot', 'Bingbot', 'OAI-SearchBot') as $bot) {
        if (yeez_wp_robots_blocks($robots, $bot)) $blocked[] = $bot;
    }
    $pages = array();
    foreach (array('about' => array('about', 'about-us'), 'contact' => array('contact', 'contact-us'), 'editorial_policy' => array('editorial-policy', 'editorial-standards', 'ai-policy'), 'corrections' => array('corrections', 'corrections-policy')) as $k => $slugs) {
        $pages[$k] = false;
        foreach ($slugs as $sl) { $pg = get_page_by_path($sl); if ($pg && $pg->post_status === 'publish') { $pages[$k] = get_permalink($pg); break; } }
    }
    $authors = array();
    foreach (get_users(array('capability' => array('edit_posts'), 'fields' => array('ID', 'display_name'))) as $u) {
        $authors[] = array('name' => $u->display_name, 'has_bio' => trim((string) get_user_meta($u->ID, 'description', true)) !== '', 'page' => get_author_posts_url($u->ID));
    }
    return array(
        'plugin_version'    => YEEZ_WP_VERSION,
        'site_name'         => get_bloginfo('name'),
        'seo_plugin'        => yeez_wp_seo_plugin(),
        'search_visible'    => (bool) get_option('blog_public'),
        'sitemap'           => yeez_wp_main_sitemap(),
        'news_sitemap'      => home_url('/yeez-news-sitemap.xml'),
        'indexnow_key_file' => get_option('yeez_wp_indexnow_key') ? home_url('/' . get_option('yeez_wp_indexnow_key') . '.txt') : null,
        'robots_blocks'     => $blocked,
        'noindex_tags'      => get_option('yeez_wp_noindex_tags', '1') === '1',
        'permalinks'        => get_option('permalink_structure') ?: 'plain',
        'site_icon'         => (bool) get_site_icon_url(),
        'trust_pages'       => $pages,
        'authors'           => $authors,
    );
}

function yeez_wp_robots_blocks($txt, $bot) {
    $groups = preg_split('/\n(?=\s*user-agent:)/i', "\n" . $txt);
    $applies = array(); $star = array();
    foreach ($groups as $g) {
        if (!preg_match_all('/^\s*user-agent:\s*(.+)$/im', $g, $ua)) continue;
        $agents = array_map('strtolower', array_map('trim', $ua[1]));
        $blocks = (bool) preg_match('/^\s*disallow:\s*\/\s*$/im', $g);
        if (in_array(strtolower($bot), $agents, true)) $applies[] = $blocks;
        elseif (in_array('*', $agents, true)) $star[] = $blocks;
    }
    $use = $applies ? $applies : $star;
    return in_array(true, $use, true);
}
