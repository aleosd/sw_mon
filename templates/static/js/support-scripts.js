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
