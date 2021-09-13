//Viz is a global object and it is created once.
var viz;

$(document).ready(function () {
    var query = "MATCH (p:Project)-[r:includes]-(k:Keyphrase) "
        + "WHERE k.pagerank > 200 "
        + "RETURN p,r,k LIMIT 1000";
    draw(query);
});

$("#query").click(function () {
    var start = $("#field1").val();
    var end = $("#field2").val();
    var score = $("#field3").val();
    if (start === "" || end === "") {
        alert("Please speficy the ranges");
        return;
    }
    // Build the query based on the above values.
    var query = "MATCH (p:Project)-[r:includes]-(k:Keyphrase) "
        + "WHERE k.pagerank > " + start + " "
        + "AND k.pagerank < " + end + " "
        + "RETURN p,r,k LIMIT 1000";
    viz.renderWithCypher(query);
});

$("#stabilize").click(function () {
    viz.stabilize();
})

$("#textarea").keyup(function (e) {
    var code = e.keyCode ? e.keyCode : e.which;
    if (code === 13) { // Enter key pressed.
        var query = $("#textarea").val().replace(/\r?\n|\r/g, "");
        // Set value back to retain the query 
        // without any newline characters.
        $("#textarea").val(query);
        if (query === ""){
            alert("Please supply a query!");
            return;
        }
        viz.renderWithCypher(query);
        return;
    }
});

function draw(query) {
    // Create a config object for viz.
    var config = {
        container_id: "viz",
        server_url: "bolt://localhost:7687",
        server_user: "neo4j",
        server_password: "123",
        labels: {
            "Keyphrase": {
                caption: "name",
                size: "pagerank",
                community: "community"
            },
            "Organization": {
                caption: "name",
                size: "none",
                community: "community"
            },
            "Project": {
                caption: "acronym",
                size: "none",
                community: "community"
            }
        },
        relationships: {
            "includes": {
                caption: "none",
                thickness: "none"
            },
            "participates_in": {
                caption: "none",
                thickness: "none"
            },
            "coordinates": {
                caption: "none",
                thickness: "none"
            },
            "is_similar": {
                caption: "score",
                thickness: "score"
            }
        },
        initial_cypher: query
    }
    viz = new NeoVis.default(config);
    viz.render();
    return 
}
