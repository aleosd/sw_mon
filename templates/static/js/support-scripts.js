// Search-filter script for table
$(document).ready(function() {
    // Key pressed in search field, filter table
    $('#search').on('keyup', function() {
        var query = $(this).val();
        $('#sw_table tbody tr').each(function(e) {
            if (!query || $(this).children('#sw_addr, #sw_ip, #sw_type').text().toLowerCase().indexOf(query) > -1)
                $(this).show();
            else
                $(this).hide();
        });
    });
});

// Warn-Err views builder for table 
$(document).ready(function() {
    $('#warn').click(function() {
        $(this).addClass('active');
        $('#all').removeClass('active');
        $('#err').removeClass('active');
        $('#sw_table tbody tr').each(function(e) {
            if ($(this).hasClass('warning'))
                $(this).show();
            else
                $(this).hide();
        });
    });
    $('#err').click(function() {
        $(this).addClass('active');
        $('#all').removeClass('active');
        $('#warn').removeClass('active');
        $('#sw_table tbody tr').each(function(e) {
            if ($(this).hasClass('error'))
                $(this).show();
            else
                $(this).hide();
        });
    });

});

// table-sorting script
// $(document).ready(function()
//    {
//        $("#sw_table").tablesorter({sortList: [[0,0]]});
//    }
// );
